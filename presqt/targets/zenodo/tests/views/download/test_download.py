import io
import json
import shutil
import zipfile
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from presqt.api_v1.utilities import hash_tokens
from presqt.utilities import read_file
from presqt.targets.utilities import shared_call_get_resource_zip

from config.settings.base import ZENODO_TEST_USER_TOKEN


class TestDownload(SimpleTestCase):
    """
    Test the 'api_v1/downloads/<ticket_id>/' endpoint's GET method.

    Testing only Zenodo download function.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': ZENODO_TEST_USER_TOKEN,
                       'HTTP_PRESQT_EMAIL_OPT_IN': ''}
        self.target_name = 'zenodo'
        self.token = ZENODO_TEST_USER_TOKEN

    def test_success_download_project(self):
        """
        Return a 200 along with a zip file of the private repo requested.
        """
        resource_id = '3525310'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 15)

        # Verify the fixity file has the two file entries
        with zip_file.open('zenodo_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 2)

        file_path_one = "{}_download_{}/data/Test PresQT Project/1900s_Cat.jpg".format(
            self.target_name, resource_id)
        file_path_two = "{}_download_{}/data/Test PresQT Project/asdf.png".format(self.target_name,
                                                                                  resource_id)
        # Verify that the files exists
        self.assertIn(file_path_one, zip_file.namelist())
        self.assertIn(file_path_two, zip_file.namelist())

        # Verify there is only two entry that contains this folder
        count_of_file_references = zip_file.namelist().count(file_path_one)
        self.assertEqual(count_of_file_references, 1)

        count_of_file_references = zip_file.namelist().count(file_path_two)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_download_public_project(self):
        """
        Return a 200 along with a zip file of the private repo requested.
        """
        resource_id = '2441380'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 14)

        # Verify the fixity file has the one file entry
        with zip_file.open('zenodo_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        with zip_file.open('zenodo_download_{}/PRESQT_FTS_METADATA.json'.format(resource_id)) as metadatafile:
            extra_metadata = json.load(metadatafile)['extra_metadata']
            self.assertEqual(extra_metadata['title'], "A Curious Egg")
            self.assertEqual(extra_metadata['description'], 'n/a')
            self.assertEqual(extra_metadata['creators'],
                             [{'first_name': 'Barnard,', 'last_name': 'E. E.', 'ORCID': None}])
            self.assertEqual(extra_metadata['license'], 'CC0-1.0')
            self.assertEqual(extra_metadata['related_identifiers'],
                             [{'type':'doi', 'id':'10.1126/science.os-2.49.256'}])
            self.assertEqual(extra_metadata['publication_date'], '1881-05-28')

        file_path = "{}_download_{}/data/A Curious Egg/article.pdf".format(
            self.target_name, resource_id)
        # Verify that the files exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only two entry that contains this folder
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_download_file(self):
        """
        Return a 200 along with a zip file of the file requested.
        """
        resource_id = 'dea4211e-e240-4b2c-aede-c6c0eb84c9a0'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the fixity file has the one file entry
        with zip_file.open('zenodo_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/asdf.png".format(
            self.target_name, resource_id)
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only one entry that contains this file
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_success_download_public_file(self):
        """
        Return a 200 along with a zip file of the public file requested.
        """
        resource_id = '7c2a7648-44ec-4f17-98a1-b1736761d59b'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('job_status', kwargs={'action': 'download',
                                            'response_format': 'zip'})
        response = self.client.get(url, **self.header)
        # Verify the status code
        self.assertEqual(response.status_code, 200)

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Verify the name of the zip file
        self.assertEquals(
            response._headers['content-disposition'][1],
            'attachment; filename={}_download_{}.zip'.format(self.target_name, resource_id))
        # Verify content type
        self.assertEqual(response._headers['content-type'][1], 'application/zip')
        # Verify the number of resources in the zip is correct
        self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the fixity file has the one file entry
        with zip_file.open('zenodo_download_{}/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/article.pdf".format(
            self.target_name, resource_id)
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only one entry that contains this file
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(self.ticket_number))

    def test_error_500_401(self):
        """
        Return a 500 if an invalid token is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '209373160',
                                          'resource_format': 'zip'})

        response = self.client.get(
            url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs', 'HTTP_PRESQT_EMAIL_OPT_IN': ''})
        ticket_number = hash_tokens('eggs')
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 401)
        self.assertEqual(download_response.data['message'],
                         "Token is invalid. Response returned a 401 status code.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))

    def test_error_500_404(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        # First we will check an invalid project id
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '8219237',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        ticket_number = hash_tokens(self.token)
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **self.header)
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 404)
        self.assertEqual(download_response.data['message'],
                         "The resource with id, 8219237, does not exist for this user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))

        # Now we will check an invalid file id
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '127eqdid-WQD2EQDWS-dw234dwd8',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/jobs/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['resource_download']['status'] == 'in_progress':
            try:
                process_info = read_file(process_info_path, True)
            except json.decoder.JSONDecodeError:
                # Pass while the process_info file is being written to
                pass

        download_response = self.client.get(download_url, **self.header)
        # The endpoint lumps all errors into a 500 status code
        self.assertEqual(download_response.status_code, 500)
        self.assertEqual(download_response.data['status_code'], 404)
        self.assertEqual(download_response.data['message'],
                         "The resource with id, 127eqdid-WQD2EQDWS-dw234dwd8, does not exist for this user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/jobs/{}'.format(ticket_number))
