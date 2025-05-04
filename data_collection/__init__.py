"""Adapted from Gyori Lab Indra Cogex (specifically, src/indra_cogex/sources/nih_reporter/__init__.py)
Title: __init__.py
Author: Owen Sharpe
Description: using the NIHReporterDownloader (adapted from the NIHReporterProcessor created by Gyori Lab)
to extract all files from the NIH Reporter Database
Data will be pushed to the 'nih_reporter_website_data' folder

Downloader for the NIH RePORTER data set.

NIH RePORTER is available at https://reporter.nih.gov/. Export for bulk
downloads at: https://reporter.nih.gov/exporter available as zipped csv files per year:

- Projects: table of basic project metadata including activity code,
  various dates, PI code and names, organization info, total cost, etc.
- Publications: table of publications including PMID, PMCID, author lists,
  affiliations etc. but no link to each project. This information is
  usually available via PubMed directly.
- Publication links: table with two columns linking each PMID with a
  project number. The relationship is many-to-many.
- Project abstracts: table with two columns, application ID and corresponding
  abstract.
- Patents: table with patent IDs, titles, linked to project IDs and
  the patent organization name
- Clinical trials: table with core project number, clinical trials ID, study
  name and study status.

"""

import re
import logging
import datetime
from typing import Iterable, Any
import zipfile
from collections import defaultdict
import pandas
import pystow
import os
from pathlib import Path


logger = logging.getLogger(__name__)


# Regular expressions to find files of different types
fname_prefixes = {
    "project": "RePORTER_PRJ_C_FY",
    "publink": "RePORTER_PUBLINK_C_",
    "abstract": "RePORTER_PRJABS_C_FY",
    "patent": "Patents_",
    "clinical_trial": "ClinicalStudies_",
}


fname_regexes = {
    "project": re.compile(rf"{fname_prefixes['project']}(\d+)\.zip"),
    "publink": re.compile(rf"{fname_prefixes['publink']}(\d+)\.zip"),
    "abstract": re.compile(rf"{fname_prefixes['abstract']}(\d+)\.zip"),
    "patent": re.compile(rf"{fname_prefixes['patent']}(\d+)\.csv"),
    "clinical_trial": re.compile(rf"{fname_prefixes['clinical_trial']}(\d+)\.csv"),
}

base_url = "https://reporter.nih.gov/exporter"

# including abstracts
download_urls = {
    "project": f"{base_url}/projects/download/%s",
    "abstract": f"{base_url}/abstracts/download/%s",
    "publink": f"{base_url}/linktables/download/%s",
    "clinical_trial": f"{base_url}/clinicalstudies/download",
    "patent": f"{base_url}/patents/download",
}


# Project columns to include as node attributes, note that not all columns
# are included here.
project_columns = [
    'ACTIVITY', 'ADMINISTERING_IC', 'AWARD_NOTICE_DATE',
    'BUDGET_END', 'BUDGET_START', 'CORE_PROJECT_NUM', 'DIRECT_COST_AMT',
    'FY', 'ORG_CITY', 'ORG_COUNTRY', 'ORG_DEPT', 'ORG_DISTRICT',
    'ORG_NAME', 'PI_IDS', 'PI_NAMEs', 'PROJECT_END', 'PROJECT_START',
    'PROJECT_TITLE', 'TOTAL_COST']


class NihReporterDownloader():
    """Downloader for NIH Reporter database."""

    name = "nih_reporter"

    def __init__(self, download=True, force_download=False):

        # make the directory for the data
        project_dir = Path(__file__).resolve().parent.parent
        base_folder_path = project_dir / "data_collection"
        base_folder_path.mkdir(parents=True, exist_ok=True)

        # set pystow directory
        os.environ['PYSTOW_HOME'] = str(base_folder_path)

        # now make directory for data
        self.base_folder = pystow.module("nih_reporter_website_data")

        # create dictionary for the data files
        data_files = defaultdict(dict)

        # Download the data files if they are not present
        if download or force_download:
            last_year = datetime.datetime.now().year - 1
            logger.info(
                "Downloading NIH RePORTER data files %s force redownload..."
                % ("with" if force_download else "without")
            )
            self.download_files(force=force_download, last_year=last_year)

        # Collect all the data files
        for file_path in self.base_folder.base.iterdir():
            for file_type, pattern in fname_regexes.items():
                match = pattern.match(file_path.name)
                if match:
                    data_files[file_type][match.groups()[0]] = file_path
                    break
        self.data_files = dict(data_files)
        self._core_project_applications = defaultdict(list)

    def download_files(self, force=False, first_year=1985, last_year=2025):
        current_year = datetime.date.today().year
        for subset, url_pattern in download_urls.items():
            # These files are indexed by year
            if subset in ["project", "publink", "abstract"]:
                for year in range(first_year, last_year + 1):
                    url = download_urls[subset] % year
                    self.base_folder.ensure(
                        url=url,
                        name=fname_prefixes[subset] + str(year) + ".zip",
                        force=force,
                    )
            # These files are single downloads but RePORTER adds a timestamp
            # to the file name making it difficult to check if it already exists
            # so to avoid always redownloading, we take Jan 1st of the current
            # year as reference.
            else:
                timestamp = int(
                    datetime.datetime(year=current_year, month=1, day=1).timestamp()
                )
                url = download_urls[subset]
                self.base_folder.ensure(
                    url=url,
                    name=fname_prefixes[subset] + str(timestamp) + ".csv",
                    force=force,
                )

    def run(self):
        """Run the downloader and print summary information."""
        # summary of downloaded files
        print(f"NIH Reporter data downloaded to: {self.base_folder.base}")
        for file_type, files in self.data_files.items():
            print(f"Downloaded {len(files)} {file_type} file(s)")
        return 0


def clean_text(text: Any) -> Any:
    """Escape newlines, carriage returns and single quotes from text"""
    if isinstance(text, str):
        return \
            text.replace("\n", "\\n") \
                .replace("\r", "\\r") \
                .replace("'", "\\'").strip()
    return text


def newline_escape(text: Any) -> Any:
    """Escape newlines from text"""
    if isinstance(text, str):
        return text.replace("\n", "\\n")
    return text


def main():
    downloader = NihReporterDownloader()
    print("Downloading Files from the NIH Exporter...")
    return downloader.run()


if __name__ == "__main__":
    exit(main())
