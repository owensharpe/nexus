# Nexus
## Data Annotator
Nexus is a Python-based tool for extracting, annotating, and analyzing NIH grant project data. It leverages Indra for downloading the NIH data and Gilda for entity recognition and annotation of project titles and abstracts, enabling structured insights from large-scale NIH datasets.

- Parses and processes NIH grant data from CSV files using Indra
- Uses Gilda for named entity recognition in project titles and abstracts
- Creates annotations in JSONL format for easy processing
- Handles missing data and ensures clean text processing
- Turns all data into node and edge relationships for Neo4j database


### Phase 1: Data Collection

#### Tools Related to Neo4j Data Analysis:
`__init__.py` - Indra Cogex file with functions to pull data files directly from NIH website.

`__main__.py` - Utilizes `__init__.py` to automate data collection from the NIH website.


#### Tools Related to the NIH RePORTER API:
`nih_reporter_api.py` - Utilizes tools offered from the NIH RePORTER API by being a class to extract data from the NIH RePORTER database.

`automate_data_extraction.py` - Uses functions from `nih_reporter_api.py` to automate a data extraction process from API.


### Phase 2: Data Preprocessing
`01_extracting_bio_ontologies.py` - Extracts relevant bio-ontologies from the NIH database research project abstracts using Gilda.

`02_creating_nodes_and_relations.py` - Creating the node and edge relationships for Neo4j given the proper data.


### Phase 3: Neo4j Database Creation
`Dockerfile` - builds necessary components for the database.

`startup.sh` - starts the database with bash.


### Additional Information For Those Wanting to View NIH RePORTER API:
For more, specific, information on the NIH RePORTER API usage, refer to this PDF made by the creators of the database: https://api.reporter.nih.gov/documents/Data%20Elements%20for%20RePORTER%20Project%20API_V2.pdf

#### Calling 'Publications'
###### Input Parameters:
    :param application_ids: user inputted application ids
    :param pmids: user inputted pubmed identifiers
    :param core_proj_nums: user inputted core project numbers
    :param limit: the specific publication to start at (e.g., 59 starts at publication #60)
    :param offset: amount of publications to grab (max 500)
    :param sort_field: sort the field by a criterion (should be a parameter in 'inc_fields')

###### Available Output Responses:
    :return Core Project Number
    :return PMID
    :return Latest Application ID


#### Calling 'Projects'
###### Input Parameters:
    :param inc_fields: specify the include fields for projects
    :param exc_fields: specify the exclude fields for projects
    :param offset: amount of publications to grab (max 500)
    :param limit: the specific publication to start at (e.g., 59 starts at publication #60)
    :param sort_field: sort the field by a criterion
    :param use_relevance: bring the most closely matching records with the search criteria on top
    :param fiscal_years: retrieve projects that correspond to one of the fiscal years entered
    :param include_active_projects: option to return active projects or exclude them
    :param pi_names: projects associated with any of the PI names passed
    :param po_names: projects associated with any of the PO names passed
    :param org_names: projects associated with any of the organization names passed
    :param org_names_exact_match: exactly match with organization names
    :param pi_profile_ids: projects associated with any of the project investigator profile Ids passed
    :param org_cities: projects associated with any of the organization cities passed
    :param org_states: projects associated with any of the organization states passed
    :param project_nums: projects associated with any of the project numbers passed
    :param project_num_split: projects matching all specified criteria
    :param spending_categories: projects associated with any of the spending categories passed
    :param funding_mechanism: projects associated with any of the funding mechanism passed
    :param org_countries: projects associated with any of the organization countries passed
    :param appl_ids: projects associated with any of the application IDs passed
    :param agencies: projects associated with any of the agencies passed
    :param is_agency_admin: filter the projects for admin agency status
    :param is_agency_funding: filter if agency is funding
    :param activity_codes: projects associated with any of the activity codes passed
    :param award_types: projects associated with any of the award types passed
    :param dept_types: projects associated with any of the dept types passed
    :param cong_dists: projects associated with any of the cong dists passed
    :param opportunity_numbers: projects associated with any of the opportunity numbers passed
    :param project_start_date: filter the projects that starts within a specific duration
    :param project_end_date: filter the projects that end within a specific duration
    :param organization_type: projects associated with any of the organization_type passed
    :param award_notice_date: projects within specified award notice dates
    :param award_amount_range: projects awarded within specified amount range
    :param exclude_subprojects: retrieve the associated projects with a selected value (true/false)
    :param multi_pi_only: retrieve the associated projects with selected value (true/false)
    :param newly_added_projects_only: retrieve the associated projects with a selected value (true/false)
    :param sub_project_only: retrieve the associated projects with a selected value (true/false
    :param covid_response: retrieve projects awarded to study COVID-19 and related topics
    :param date_added: filter the projects that are added to RePORTER within a specific duration

###### Available Output Responses:
Project

    :return IC
    :return Support Year
    :return Application Type Code
    :return Activity Code
    :return Serial Number
    :return Suffix Code
    :return Project Number
    :return Core Project Number
    :return Project Start Date
    :return Project End Date
    :return Sub-Project ID
    :return Abstract
    :return Title
    :return Public Health Relevance
    :return RCDC Terms
    
Study Section

    :return SRG Code
    :return SRG Flex
    :return SRA Designator Code
    :return SRA Flex Code
    :return Group Code
    :return Study Section Name
    
Personnel

    :return Principal Investigators
    :return Program Officers
    
Funded Organizations

    :return Congressional District
    :return Organization Type
    :return Organization Name
    :return Organization City
    :return Organization State
    :return Organization ZIP
    :return Organization Country
    :return Organization Department
    :return Organization DUNS number
    :return Organization UEI
    :return Organization ID (IPF)
    :return FIPS 
    
Project Funding

    :return Award Notice Date
    :return Fiscal Year
    :return Opportunity Number
    :return Award Amount
    :return NIH COVID-19 Response
    :return ARRA Indicator
    :return CFDA Code
    :return Funding Mechanism
    :return Direct Costs
    :return Indirect Costs
    :return Budget Start Date
    :return Budget End Date
