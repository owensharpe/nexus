"""
File: 01_extracting_bio_ontologies.py
Author: Owen Sharpe
Description: Extracting relevant bio-ontologies from the NIH database research project abstracts using Gilda (Gyori Lab)
"""

# import libraries
import pandas as pd
import os
import json
import numpy as np
from tqdm import tqdm
import nltk
import gilda
import argparse
from pathlib import Path
import indra_cogex.sources.nih_reporter


def parse_args():
    parser = argparse.ArgumentParser(description="Extract and annotate NIH project abstracts with Gilda")
    parser.add_argument("--input_dir", required=True, help="Directory containing the NIH zip files")
    parser.add_argument("--output_file", default="annotations.jsonl", help="Path to save annotated output file")
    return parser.parse_args()


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # download nltk stopwords
    nltk.download('stopwords')

    # initialize data collectors
    project_list, publication_list, abstract_list = [], [], []

    nih = indra_cogex.sources.nih_reporter

    for file in input_dir.glob("*.zip"):
        if "PRJ_C" in file.name:
            project_list.append(nih._read_first_df(str(file)))
        elif "PUBLINK_C" in file.name:
            publication_list.append(nih._read_first_df(str(file)))
        elif "PRJABS_C" in file.name:
            abstract_list.append(nih._read_first_df(str(file)))

    # create large dataframes
    projects = pd.concat(project_list)
    publications = pd.concat(publication_list)
    abstracts = pd.concat(abstract_list)

    # clean data
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
