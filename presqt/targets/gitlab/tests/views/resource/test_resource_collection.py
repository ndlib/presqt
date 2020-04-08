from django.test import SimpleTestCase
from rest_framework.test import APIClient
from rest_framework.reverse import reverse

from config.settings.base import GITLAB_TEST_USER_TOKEN


class TestResourceCollection(SimpleTestCase):
    """
    Test the 'api_v1/targets/gitlab/resources' endpoint's GET method.

    Testing GitLab integration.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}

    def test_success_gitlab(self):
        """
        Return a 200 if the GET method is successful when grabbing GitLab resources.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))
        # Verify the count of resource objects is what we expect.
        self.assertEqual(len(response.data), 21)

        for data in response.data:
            self.assertEqual(len(data['links']), 1)

    def test_success_gitlab_with_search(self):
        """
        Return a 200 if the GET method is successful when grabbing GitLab resources with search
        parameters.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?title=A+Good+Egg', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))


        ###### Search by ID #######
        response = self.client.get(url + '?id=17990806', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        #### Search by Author ####
        response = self.client.get(url + '?author=prometheus-test', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

        ### Search by General ###
        response = self.client.get(url + '?general=egg', **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)
        # Verify the dict keys match what we expect
        keys = ['kind', 'kind_name', 'id', 'container', 'title', 'links']
        for data in response.data:
            self.assertListEqual(keys, list(data.keys()))

    def test_error_400_missing_token_gitlab(self):
        """
        Return a 400 if the GET method fails because the presqt-source-token was not provided.
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url)
        # Verify the error status code and message
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'error': "PresQT Error: 'presqt-source-token' missing in the request headers."})

    def test_error_401_invalid_token_gitlab(self):
        """
        Return a 401 if the token provided is not a valid token.
        """
        client = APIClient()
        header = {'HTTP_PRESQT_SOURCE_TOKEN': 'eggyboi'}
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = client.get(url, **header)
        # Verify the error status code and message.
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data,
                         {'error': "Token is invalid. Response returned a 401 status code."})

    def test_error_400_bad_search_parameters(self):
        """
        Test for a 400 with a bad parameter
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        # TOO MANY KEYS
        response = self.client.get(url + '?title=hat&spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

        # BAD KEY
        response = self.client.get(url + '?spaghetti=egg', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: GitLab does not support spaghetti as a search parameter.')
        self.assertEqual(response.status_code, 400)

        # SPECIAL CHARACTERS IN REQUEST
        response = self.client.get(url + '?title=egg:boi', **self.header)

        self.assertEqual(response.data['error'], 'PresQT Error: The search query is not formatted correctly.')
        self.assertEqual(response.status_code, 400)

    def test_for_id_search_no_results_gitlab(self):
        """
        Test for a successful id search but for an id that doesn't exist
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?id=supasupabadid', **self.header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_for_author_search_no_results_gitlab(self):
        """
        Test for a successful author search but for an author that doesn't exist
        """
        url = reverse('resource_collection', kwargs={'target_name': 'gitlab'})
        response = self.client.get(url + '?author=XxsupasupasupasupabadauthorxX', **self.header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])