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
    parser.add_argument("--input", required=True, help="Path to the annotations.jsonl file")
    parser.add_argument("--output_dir", default="prepped_data", help="Directory to save output TSV files")
    return parser.parse_args()


def main():
    args = parse_args()

    file_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # count total lines
    with file_path.open("r", encoding="utf-8") as file:
        total_lines = sum(1 for _ in file)

    print("Creating Project and Term Nodes as well as Edges...")

    applications = []
    terms = {}
    relationships = []

    with file_path.open("r", encoding="utf-8") as file:
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

            applications.append({"id:ID": f"nihreporter.project:{app_id}", ":LABEL": "ResearchProject"})
            terms.update(top_terms)

            for curie in top_terms:
                relationships.append({
                    ":START_ID": f"nihreporter.project:{app_id}",
                    ":END_ID": bioregistry.normalize_curie(curie),
                    ":TYPE": "has_grounded_term"
                })

    project_nodes = pd.DataFrame(applications).drop_duplicates()
    term_nodes = pd.DataFrame(
        [{"id:ID": bioregistry.normalize_curie(curie), "name": name, ":LABEL": "BioEntity"}
         for curie, name in terms.items()]
    )
    relationship_edges = pd.DataFrame(relationships)

    # Save to gzipped TSVs
    project_nodes.to_csv(output_dir / 'research_project_nodes.tsv.gz', sep='\t', index=False, compression="gzip")
    term_nodes.to_csv(output_dir / 'bio_entity_nodes.tsv.gz', sep='\t', index=False, compression="gzip")
    relationship_edges.to_csv(output_dir / 'edges.tsv.gz', sep='\t', index=False, compression="gzip")


if __name__ == '__main__':
    main()
