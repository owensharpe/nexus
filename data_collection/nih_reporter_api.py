"""
Title: nih_reporter_api.py
Author: Owen Sharpe
Description: creating an API class to extract data from the NIH RePORTER database API.
"""

# import libraries
import requests


class NIHReporterAPI:
    def __init__(self):
        # our base private instance variables
        self.base_url = "https://api.reporter.nih.gov/v2/"
        self.headers = {"Content-Type": "application/json"}

    def _make_api_call(self, endpoint, payload):
        """
        explanation: calls the NIH RePORTER API and if successful, returns the required data
        :param endpoint: specified endpoint (will be 'projects' or 'publications')
        :param payload: user specified parameters for the api call
        :return: a dictionary which will be the output of the api call response 'results' section
        """

        # try to make api call request
        try:
            url = self.base_url + endpoint
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()['results']  # return
        except requests.exceptions.RequestException as e:  # if we're cast with an error
            print(f"Error: {e}")
            return None

    def get_publications(self, offset=0, limit=10, sort_field="appl_ids", **criteria):
        """
        calls the 'publications' search request of the NIH RePORTER API
        :param offset: amount of publications to grab (max 500)
        :param limit: the specific publication to start at (e.g., 59 starts at publication #60)
        :param sort_field: sort the field by a criterion (should be a parameter in 'inc_fields')
        :param criteria: a 'kwargs' parameter for user specified parameters to filter search results (info in README)
        :return: 'publications' api response call
        """

        # the 'publications' payload criteria (with user specified parameters)
        payload = {
            "criteria": criteria,
            "offset": offset,
            "limit": limit,
            "sort_field": sort_field,
            "sort_order": "asc"  # sort ascending ('asc') or descending ('desc')
        }
        return self._make_api_call("publications/search", payload)

    def get_projects(self, inc_fields=[], exc_fields=[], offset=0, limit=10, sort_field="appl_id", **criteria):
        """
        calls the 'projects' search request of the NIH RePORTER API
        :param inc_fields: specify the included fields for the 'projects' api call request
        :param exc_fields: specify the excluded fields for the 'projects' api call request
        :param offset: amount of publications to grab (max 500)
        :param limit: the specific publication to start at (e.g., 59 starts at publication #60)
        :param sort_field: sort the field by a criterion (should be a parameter in 'inc_fields')
        :param criteria: a 'kwargs' parameter for user specified parameters to filter search results (info in README)
        :return: 'projects' api response call
        """

        # the 'projects' payload criteria (with user specified parameters)
        payload = {
            "criteria": criteria,
            "include_fields": inc_fields,
            "exclude_fields": exc_fields,
            "offset": offset,
            "limit": limit,
            "sort_field": sort_field,
            "sort_order": "asc"  # sort ascending ('asc') or descending ('desc')
        }
        return self._make_api_call("projects/search", payload)
