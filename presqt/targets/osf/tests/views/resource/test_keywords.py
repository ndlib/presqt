import json
import requests
from unittest.mock import patch

from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from django.test import SimpleTestCase

from config.settings.base import OSF_TEST_USER_TOKEN


class TestResourceKeywords(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}/keywords/` endpoint's GET method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.keys = ['tags', 'keywords']

    def test_success_project_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting an OSF `project`.
        """
        resource_id = 'cmn5z'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual keywords
        self.assertIn('eggs', response.data['tags'])
        self.assertIn('water', response.data['tags'])
        self.assertIn('animals', response.data['tags'])

    def test_success_file_keywords(self):
        """
        Returns a 200 if the GET method is successful when getting an OSF `file`.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Spot check some individual keywords
        self.assertIn('eggs', response.data['tags'])
        self.assertIn('water', response.data['tags'])
        self.assertIn('animals', response.data['tags'])
        self.assertIn('PresQT', response.data['tags'])

    def test_error_storage_keywords(self):
        """
        Returns a 400 if the GET method is unsuccessful when getting an OSF `storage` keywords.
        """
        resource_id = "cmn5z:googledrive"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'], "OSF Storages do not have keywords.")

    def test_invalid_token(self):
        """
        Returns a 401 if token is bad.
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'EGGS'}
        resource_id = "cmn5z:googledrive"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")


class TestResourceKeywordsPOST(SimpleTestCase):
    """
    Test the `api_v1/targets/osf/resources/{resource_id}/keywords/` endpoint's POST method.

    Testing OSF integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': OSF_TEST_USER_TOKEN}
        self.keys = ['updated_keywords']

    def test_invalid_token(self):
        """
        Returns a 401 if token is bad.
        """
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': 'EGGS'}
        resource_id = "cmn5z"
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 401)
        # Verify the error message
        self.assertEqual(response.data['error'],
                         "Token is invalid. Response returned a 401 status code.")

    def test_success_project_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a OSF `project` keywords.
        """
        resource_id = 'cmn5z'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)
        # Get the ount of the initial keywords
        initial_keywords = len(get_response.data['tags'])

        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is larger than the initial one.
        self.assertGreater(len(response.data['updated_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN),
                   'Content-Type': 'application/json'}
        patch_url = 'https://api.osf.io/v2/nodes/{}/'.format(resource_id)
        data = {"data": {"type": "nodes", "id": resource_id, "attributes": {
            "tags": ['eggs', 'water', 'animals']}}}

        response = requests.patch(patch_url, headers=headers, data=json.dumps(data))

        self.assertEqual(response.status_code, 200)

    def test_success_file_keywords(self):
        """
        Returns a 202 if the POST method is successful when updating a OSF `file` keywords.
        """
        resource_id = '5cd9831c054f5b001a5ca2af'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        # First check the initial tags.
        get_response = self.client.get(url, **self.header)
        # Get the ount of the initial keywords
        initial_keywords = len(get_response.data['tags'])

        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 202)
        # Verify the dict keys match what we expect
        self.assertListEqual(self.keys, list(response.data.keys()))
        # Ensure the new list is larger than the initial one.
        self.assertGreater(len(response.data['updated_keywords']), initial_keywords)

        # Set the project keywords back to what they were.
        headers = {'Authorization': 'Bearer {}'.format(OSF_TEST_USER_TOKEN),
                   'Content-Type': 'application/json'}
        patch_url = 'https://api.osf.io/v2/files/{}/'.format(resource_id)
        data = {"data": {"type": "files", "id": resource_id, "attributes": {
            "tags": ['eggs', 'water', 'animals', 'PresQT']}}}

        response = requests.patch(patch_url, headers=headers, data=json.dumps(data))

        self.assertEqual(response.status_code, 200)

    def test_error_storage_keywords(self):
        """
        Returns a 400 if the POST method is unsuccessful when getting a GitLab `file` keywords.
        """
        resource_id = 'cmn5z:googledrive'
        url = reverse('keywords', kwargs={'target_name': 'osf',
                                          'resource_id': resource_id})
        response = self.client.post(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 400)
        # Verify the error message
        self.assertEqual(response.data['error'], "OSF Storages do not have keywords.")

    def test_failed_update_keywords_project(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)
        with patch('requests.patch') as mock_request:
            mock_request.return_value = mock_req
            # Upload new keywords
            resource_id = 'cmn5z'
            url = reverse('keywords', kwargs={'target_name': 'osf',
                                              'resource_id': resource_id})
            response = self.client.post(url, **self.header)

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "OSF returned a 500 error trying to update keywords.")

    def test_failed_update_keywords_files(self):
        # Mock a server error for when a put request is made.
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code
        mock_req = MockResponse({'error': 'The server is down.'}, 500)
        with patch('requests.patch') as mock_request:
            mock_request.return_value = mock_req
            # Upload new keywords
            resource_id = '5cd9831c054f5b001a5ca2af'
            url = reverse('keywords', kwargs={'target_name': 'osf',
                                              'resource_id': resource_id})
            response = self.client.post(url, **self.header)

            # Verify the status code
            self.assertEqual(response.status_code, 400)

            # Ensure the error is what we're expecting.
            self.assertEqual(response.data['error'],
                             "OSF returned a 500 error trying to update keywords.")
