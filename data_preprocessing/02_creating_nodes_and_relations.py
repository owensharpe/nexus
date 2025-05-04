"""
File: 02_creating_nodes_relations.py
Author: Owen Sharpe
Description: Creating the node and edge relationships for Neo4j given the proper data.
"""

# import libraries
import pandas as pd
import json
from tqdm import tqdm
import bioregistry
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Process NIH project annotations")
    parser.add_argument("--input_dir", default="temp_data_storage", help="Path to data")
    parser.add_argument("--output_dir", default="prepped_data", help="Directory to save output TSV files")
    return parser.parse_args()


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # load patent, clinical trial, and publication data
    print("Reading in data from temp_data_storage...")
    patents = pd.read_csv(input_dir / 'patents_data.tsv.gz', sep='\t', compression='gzip')
    clinical_trials = pd.read_csv(input_dir / 'clinical_trials_data.tsv.gz', sep='\t', compression='gzip')
    publications = pd.read_csv(input_dir / 'publications_data.tsv.gz', sep='\t', compression='gzip')

    # we'll use this data to add information into our project nodes
    print("Making lookup dictionary for project IDs...")
    additional_research_proj_data = (pd.read_csv(input_dir / 'temp_project_data.tsv.gz', sep='\t', compression='gzip',
                                                 low_memory=False)).set_index('APPLICATION_ID').to_dict('index')
    core_project_to_app_ids = {}
    for app_id, project_data in additional_research_proj_data.items():
        core_project_num = project_data.get('CORE_PROJECT_NUM', '')
        if core_project_num:
            if core_project_num not in core_project_to_app_ids:
                core_project_to_app_ids[core_project_num] = []
            core_project_to_app_ids[core_project_num].append(app_id)


    # first create the patent, clinical trial, and publication nodes and relationships between projects and each
    print("Creating nodes and relationships for patents, clinical trials, and publications...")
    more_project_relationships = []

    patent_nodes = []
    for _, row in tqdm(patents.iterrows(), total=len(patents), desc="Processing Patents"):

        # fixing issues with patent titles
        patent_title = row['PATENT_TITLE'] if 'PATENT_TITLE' in row else ""
        if isinstance(patent_title, str):
            patent_title = patent_title.replace('\n', ' ').replace('\r', ' ')
        patent_node = {
            "id:ID": f"google.patent:US{row['PATENT_ID']}",
            ":LABEL": "Patent",
            "name": patent_title
        }
        patent_nodes.append(patent_node)

        # find relationships
        core_project_num = row['PROJECT_ID'] if 'PROJECT_ID' in row else None
        if pd.notna(core_project_num):
            try:
                for app_id in core_project_to_app_ids[core_project_num]:
                    more_project_relationships.append({
                        ":START_ID": f"nihreporter.project:{app_id}",
                        ":END_ID": f"google.patent:US{row['PATENT_ID']}",
                        ":TYPE": "has_patent"
                    })
            except KeyError:
                pass

    clinical_trial_nodes = []
    for _, row in tqdm(clinical_trials.iterrows(), total=len(clinical_trials), desc="Processing Clinical Trials"):
        clinical_trial_node = {
            "id:ID": f"clinicaltrials:{row['ClinicalTrials.gov ID']}",
            ":LABEL": 'ClinicalTrial',
            "study": row['Study'] if 'Study' in row else ""
        }
        clinical_trial_nodes.append(clinical_trial_node)

        # find relationships
        core_project_num = row['Core Project Number'] if 'Core Project Number' in row else None
        if pd.notna(core_project_num):
            try:
                for app_id in core_project_to_app_ids[core_project_num]:
                    more_project_relationships.append({
                        ":START_ID": f"nihreporter.project:{app_id}",
                        ":END_ID": f"clinicaltrials:{row['ClinicalTrials.gov ID']}",
                        ":TYPE": "has_clinical_trial"
                    })
            except KeyError:
                pass

    # had to do in chunks to avoid memory issues
    chunk_size = 100000
    total_chunks = len(publications) // chunk_size + (1 if len(publications) % chunk_size > 0 else 0)
    for chunk_idx in tqdm(range(total_chunks), desc="Processing Publications in Sections"):
        # get chunk
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(publications))
        chunk = publications.iloc[start_idx:end_idx]

        chunk_pub_nodes = []
        chunk_relationships = []
        for _, row in chunk.iterrows():
            pub_node = {
                "id:ID": f"pubmed:{row['PMID']}",
                ":LABEL": "Publication",
            }
            chunk_pub_nodes.append(pub_node)

            # find relationships
            core_project_num = row['PROJECT_NUMBER'] if 'PROJECT_NUMBER' in row else None
            if pd.notna(core_project_num):
                try:
                    for app_id in core_project_to_app_ids[core_project_num]:
                        chunk_relationships.append({
                            ":START_ID": f"nihreporter.project:{app_id}",
                            ":END_ID": f"pubmed:{row['PMID']}",
                            ":TYPE": "has_publication"
                        })
                except KeyError:
                    pass

        # save nodes to hard drive
        temp_pub_chunk_df = pd.DataFrame(chunk_pub_nodes)
        if chunk_idx == 0:
            temp_pub_chunk_df.to_csv(output_dir / 'publication_nodes.tsv.gz', sep='\t', index=False,
                                     compression='gzip', mode='w')
        else:
            temp_pub_chunk_df.to_csv(output_dir / 'publication_nodes.tsv.gz', sep='\t', index=False,
                                     compression='gzip', mode='a', header=False)

        # if we have relationships to add
        if chunk_relationships:
            temp_chunk_rel_df = pd.DataFrame(chunk_relationships)
            temp_chunk_rel_df.to_csv(output_dir / f'pub_project_edges_{chunk_idx}.tsv.gz', sep='\t', index=False,
                                     compression="gzip")

        # delete current memory
        del chunk, chunk_pub_nodes, chunk_relationships, temp_pub_chunk_df, temp_chunk_rel_df

    # merge relationship data
    print("Merging publication relationship files...")
    pub_edge_files = list(output_dir.glob('pub_project_edges_*.tsv.gz'))
    patent_trial_edges = pd.DataFrame(more_project_relationships)
    patent_trial_edges.to_csv(input_dir / 'patent_trial_edges.tsv.gz',
                              sep='\t', index=False, compression="gzip")

    # process publication edges in chunks and append to final file
    with open(output_dir / 'patent_trial_publink_project_edges.tsv.gz', 'wb') as merged_file:

        # write the column headers first using the patent_trial_edges, then append data
        patent_trial_edges.head(0).to_csv(merged_file, sep='\t', index=False,
                                          compression="gzip", mode='w')
        patent_trial_edges.to_csv(merged_file, sep='\t', index=False,
                                  compression="gzip", mode='a', header=False)

        # now append each publication edge file
        for edge_file in tqdm(pub_edge_files, desc="Merging publication edge files"):
            pub_edges = pd.read_csv(edge_file, sep='\t', compression='gzip')
            pub_edges.to_csv(merged_file, sep='\t', index=False,
                             compression="gzip", mode='a', header=False)
            edge_file.unlink()

    # clear memory
    del patent_trial_edges

    print("Saving additional patent and clinical trial data...")
    patent_nodes = pd.DataFrame(patent_nodes).drop_duplicates()
    clinical_trial_nodes = pd.DataFrame(clinical_trial_nodes).drop_duplicates()
    patent_nodes.to_csv(output_dir / 'patent_nodes.tsv.gz', sep='\t', index=False, compression="gzip")
    clinical_trial_nodes.to_csv(output_dir / 'clinical_trial_nodes.tsv.gz', sep='\t', index=False, compression='gzip')


    print("Creating project and term nodes as well as edges...")
    # count total lines
    with (input_dir / 'annotations.jsonl').open("r", encoding="utf-8") as file:
        total_lines = sum(1 for _ in file)

    applications = []
    terms = {}
    relationships = []

    with (input_dir / 'annotations.jsonl').open("r", encoding="utf-8") as file:
        for line in tqdm(file, total=total_lines, desc="Processing JSONL", unit=" lines"):
            record = json.loads(line)
            app_id = record["application_id"]
            annotations = record["title_annotations"] + record["abstract_annotations"]

            top_terms = {}
            for ann in annotations:
                if ann["matches"]:
                    match = ann["matches"][0]["term"]
                    curie = f"{match['db'].lower()}:{match['id']}"
                    entry_name = match["entry_name"]
                    top_terms[curie] = entry_name


            project_node = {"id:ID": f"nihreporter.project:{app_id}", ":LABEL": "ResearchProject"}
            if app_id in additional_research_proj_data:
                additional_data = additional_research_proj_data[app_id]
                project_node.update({
                    "activity": additional_data.get("ACTIVITY", ""),
                    "administering_ic": additional_data.get("ADMINISTERING_IC", ""),
                    "application_type": additional_data.get("APPLICATION_TYPE", ""),
                    "title": additional_data.get("PROJECT_TITLE", ""),
                    "fiscal_year": additional_data.get("FY", ""),
                    "project_start": additional_data.get("PROJECT_START", ""),
                    "project_end": additional_data.get("PROJECT_END", ""),
                    "budget_start": additional_data.get("BUDGET_START", ""),
                    "budget_end": additional_data.get("BUDGET_END", ""),
                    "total_cost": additional_data.get("TOTAL_COST", ""),
                    "org_name": additional_data.get("ORG_NAME", ""),
                    "org_state": additional_data.get("ORG_STATE", ""),
                    "core_project_num": additional_data.get("CORE_PROJECT_NUM", "")
                    })


            applications.append(project_node)
            terms.update(top_terms)
            for curie in top_terms:
                relationships.append({
                    ":START_ID": f"nihreporter.project:{app_id}",
                    ":END_ID": bioregistry.normalize_curie(curie),
                    ":TYPE": "has_grounded_term"
                })

    project_nodes = pd.DataFrame(applications).drop_duplicates()
    term_nodes = pd.DataFrame(
        [{"id:ID": bioregistry.normalize_curie(curie), ":LABEL": "BioEntity", "name": name}
         for curie, name in terms.items()]
    )
    entity_edges = pd.DataFrame(relationships)

    # save to gzipped TSVs
    print("Saving bio entity and project data...")
    project_nodes.to_csv(output_dir / 'research_project_nodes.tsv.gz', sep='\t', index=False, compression="gzip")
    term_nodes.to_csv(output_dir / 'bio_entity_nodes.tsv.gz', sep='\t', index=False, compression="gzip")
    entity_edges.to_csv(output_dir / 'project_entity_edges.tsv.gz', sep='\t', index=False, compression="gzip")


if __name__ == '__main__':
    main()
