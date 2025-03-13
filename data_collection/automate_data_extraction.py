"""
Title: automate_data_extraction.py
Author: Owen Sharpe
Description: using the NIH RePORTER API class to automate a data extraction process from the API.
"""

# import libraries
import os
import pandas as pd
from nih_reporter_api import NIHReporterAPI


# extracting data from the API class
def main():

    # create a client for the API
    api_client = NIHReporterAPI()

    # define parameters for the 'publications' search (add or change as needed)
    pub_limit = 500
    pub_sort_field = "appl_ids"
    pub_criteria = {}

    # extract 'publications' data by using the offset step to gather publications in batches until allotted maximum
    # the allotted amount is 10,000, so we will perform 20 batch extractions
    print("Extracting data from the NIH RePORTER API 'publications' search...")
    pub_data = []
    for i in range(20):
        pub_offset = i * 500  # jumping the offset every 500 publications
        temp_pub_batch = api_client.get_publications(offset=pub_offset, limit=pub_limit, sort_field=pub_sort_field,
                                                     **pub_criteria)
        pub_data.extend(temp_pub_batch)
        print(f"Batch {i+1}/20 completed.")
    pub_df = pd.DataFrame(pub_data)
    print("Data extracted from the NIH RePORTER API 'publications' search...")


    # define parameters for the 'projects' search (add or change as needed)
    # these are the fields chosen for the project api output (change as needed)
    inc_fields = ["ApplId", "ActivityCode", "AgencyIcAdmin", "AwardType", "AwardNoticeDate", "BudgetStart",
                  "BudgetEnd", "CfdaCode", "CoreProjectNum", "OrganizationType", "OpportunityNumber",
                  "ProjectNum", "AgencyIcFundings", "FundingMechanism", "FiscalYear", "SpendingCategoriesDesc",
                  "Organization", "PhrText", "ProjectStartDate", "ProjectEndDate", "PrefTerms", "ProjectTitle",
                  "ProjectSerialNum", "FullStudySection", "SubprojectId", "ProjectNumSplit", "DirectCostAmt",
                  "IndirectCostAmt", "AwardAmount", "IsActive", "IsNew", "AbstractText", "AgencyCode",
                  "ProjectDetailUrl", "DateAdded"]
    exc_fields = []
    pro_limit = 500
    pro_sort_field = "appl_id"
    pro_criteria = {}

    # extract 'projects' data by using the offset step to gather publications in batches until allotted maximum
    # the allotted amount is 15,000, so we will perform 30 batch extractions
    print("Extracting data from the NIH RePORTER API 'projects' search...")
    pro_data = []
    for i in range(30):
        pro_offset = i * 500  # jumping the offset every 500 projects
        temp_pro_batch = api_client.get_projects(inc_fields=inc_fields, exc_fields=exc_fields, offset=pro_offset,
                                                 limit=pro_limit, sort_field=pro_sort_field, **pro_criteria)
        pro_data.extend(temp_pro_batch)
        print(f"Batch {i+1}/30 completed.")
    pro_df = pd.DataFrame(pro_data)
    print("Data extracted from the NIH RePORTER API 'projects' search...")


    # folder for where we will output data to
    print("Creating data folder...")
    data_folder = 'api_data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # send files
    print("Sending CSV files to the data folder...")
    pub_file_path = os.path.join(data_folder, 'publication_data.csv')
    pub_df.to_csv(pub_file_path, index=False)
    pro_file_path = os.path.join(data_folder, 'project_data.csv')
    pro_df.to_csv(pro_file_path, index=False)

    print("Data sending process complete. Data extracted successfully!")


if __name__ == '__main__':
    main()
