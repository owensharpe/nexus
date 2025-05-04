"""
File: 01_extracting_bio_ontologies.py
Author: Owen Sharpe
Description: Extracting relevant bio-ontologies from the NIH database research project abstracts using Gilda (Gyori Lab)
"""

# import libraries
import pandas as pd
import json
import numpy as np
from tqdm import tqdm
import nltk
import gilda
import argparse
from pathlib import Path
import logging
import zipfile


def parse_args():
    parser = argparse.ArgumentParser(description="Extract and annotate NIH project abstracts with Gilda")
    parser.add_argument("--input_dir", default='../data_collection/nih_reporter_website_data',
                        help="Directory containing the NIH zip files")
    parser.add_argument("--output_file", default="temp_data_storage/annotations.jsonl",
                        help="Path to save annotated output file")
    return parser.parse_args()


def main():
    logging.getLogger('gilda').setLevel(logging.WARNING)
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # download nltk stopwords
    nltk.download('stopwords')

    # initialize data collectors
    project_list, publication_list, abstract_list = [], [], []

    # to read the dataframes
    def read_first_df(zip_file_path):
        """Extract a single CSV file from a zip file given its path."""
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            return pd.read_csv(
                zip_ref.open(zip_ref.filelist[0], "r"),
                encoding="latin1",
                low_memory=False,
                on_bad_lines="skip",
            )

    print("Synthesizing Zip Data...")
    for file in input_dir.glob("*.zip"):
        if "PRJ_C" in file.name:
            project_list.append(read_first_df(str(file)))
        elif "PUBLINK_C" in file.name:
            publication_list.append(read_first_df(str(file)))
        elif "PRJABS_C" in file.name:
            abstract_list.append(read_first_df(str(file)))

    # create large dataframes
    projects = pd.concat(project_list)
    publications = pd.concat(publication_list)
    abstracts = pd.concat(abstract_list)

    # move clinical trials and patents data to new folder
    print("Moving Clinical Trial and Patent Data...")
    for file in input_dir.glob("*.csv"):
        if "ClinicalStudies" in file.name:
            clinical_trial_df = pd.read_csv(file)
            clinical_trial_df.to_csv(output_path.parent / 'clinical_trials_data.tsv.gz', sep='\t', index=False, compression='gzip')
        elif "Patents" in file.name:
            patent_df = pd.read_csv(file)
            patent_df.to_csv(output_path.parent / 'patents_data.tsv.gz', sep='\t', index=False, compression='gzip')

    # move publication and additional project data to new folder
    print("Moving Publication and Additional Project Data...")
    publications.to_csv(output_path.parent / 'publications_data.tsv.gz', sep='\t', index=False, compression='gzip')
    projects.to_csv(output_path.parent / 'temp_project_data.tsv.gz', sep='\t', index=False, compression='gzip')

    # clean data
    print("Merging Projects and Abstracts...")
    abstracts = abstracts[~pd.isna(abstracts['ABSTRACT_TEXT'])]
    abstracts['ABSTRACT_TEXT'] = abstracts['ABSTRACT_TEXT'].replace({np.nan: ''})
    projects = projects[~pd.isna(projects['PROJECT_TITLE'])]

    # merge data into single dataframe
    proj_data = pd.merge(
        projects[['APPLICATION_ID', 'PROJECT_TITLE']],
        abstracts[['APPLICATION_ID', 'ABSTRACT_TEXT']],
        on='APPLICATION_ID',
        how='left'
    )

    print("Creating Annotations File...")
    with output_path.open("w", encoding="utf-8") as outfile:
        for _, row in tqdm(proj_data.iterrows(), total=len(proj_data), desc="Annotating projects"):

            abstract_text = row['ABSTRACT_TEXT']
            if pd.isna(abstract_text) or not abstract_text.strip() or len(abstract_text) < 10:
                abstract_annotations_dict = []
            else:
                abstract_annotations = gilda.annotate(abstract_text)
                abstract_annotations_dict = [ann.to_json() for ann in abstract_annotations]

            title_annotations = gilda.annotate(row['PROJECT_TITLE'])
            title_annotations_dict = [ann.to_json() for ann in title_annotations]

            temp_project_data = {
                "application_id": row["APPLICATION_ID"],
                "abstract_annotations": abstract_annotations_dict,
                "title_annotations": title_annotations_dict
            }
            outfile.write(json.dumps(temp_project_data) + "\n")


if __name__ == '__main__':
    main()
