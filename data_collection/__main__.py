"""
Title: __main__.py
Author: Owen Sharpe
Description: using the NIHReporterProcessor created by the Gyori Lab to extract all files from the NIH Reporter Database
Can be called with "python -m 'data_collection'" in the cli
Data will be pushed to the 'nih_reporter_website_data' folder
"""

# import processor
from indra_cogex.sources.nih_reporter import NihReporterProcessor

if __name__ == "__main__":

    NihReporterProcessor().cli()
