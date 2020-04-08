import io
import json
import shutil
import zipfile
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from presqt.utilities import read_file
from presqt.targets.utilities import shared_call_get_resource_zip

from config.settings.base import GITLAB_TEST_USER_TOKEN


class TestDownload(SimpleTestCase):
    """
    Test the 'api_v1/downloads/<ticket_id>/' endpoint's GET method.

    Testing only GitLab download function.
    """

    def setUp(self):
        self.client = APIClient()
        self.header = {'HTTP_PRESQT_SOURCE_TOKEN': GITLAB_TEST_USER_TOKEN}
        self.target_name = 'gitlab'

    def test_success_download_private_repo(self):
        """
        Return a 200 along with a zip file of the private project requested.
        """
        resource_id = '17990894'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number,
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

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('gitlab_download_{}/data/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/Test Project/README.md".format(
           self.target_name, resource_id)
        # Verify that the folder exists
        self.assertIn(file_path, zip_file.namelist())

        # # Verify there is only one entry that contains this folder
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
    
    def test_success_download_public_repo(self):
        """
        Return a 200 along with a zip file of the public project requested.
        """
        resource_id = '17993206'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number,
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

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('gitlab_download_{}/data/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 1)

        file_path = "{}_download_{}/data/ProjectTwo/README.md".format(
            self.target_name, resource_id)
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Verify there is only one entry that contains this file
        count_of_file_references = zip_file.namelist().count(file_path)
        self.assertEqual(count_of_file_references, 1)

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
    
    def test_success_download_unowned_public_repo(self):
        """
        Return a 200 along with a zip file of the unowned public project requested.
        """
        resource_id = '17433066'
        shared_call_get_resource_zip(self, resource_id)

        url = reverse('download_job', kwargs={'ticket_number': self.ticket_number,
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
        # self.assertEqual(len(zip_file.namelist()), 13)

        # Verify the fixity file is empty as there was nothing to check.
        with zip_file.open('gitlab_download_{}/data/fixity_info.json'.format(resource_id)) as fixityfile:
            zip_json = json.load(fixityfile)
            self.assertEqual(len(zip_json), 72)

        file_path = "gitlab_download_17433066/data/Eggs-Flutter/lib/themes/theme.dart"
        # Verify that the file exists
        self.assertIn(file_path, zip_file.namelist())

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(self.ticket_number))
    
    def test_error_500_401(self):
        """
        Return a 500 if an invalid token is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': '209373160',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **{'HTTP_PRESQT_SOURCE_TOKEN': 'eggs'})
        ticket_number = response.data['ticket_number']
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
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
        shutil.rmtree('mediafiles/downloads/{}'.format(ticket_number))

    def test_error_500_404(self):
        """
        Return a 500 if an invalid resource_id is provided.
        """
        url = reverse('resource', kwargs={'target_name': self.target_name,
                                          'resource_id': 'bad',
                                          'resource_format': 'zip'})

        response = self.client.get(url, **self.header)
        ticket_number = response.data['ticket_number']
        download_url = response.data['download_job_zip']
        process_info_path = 'mediafiles/downloads/{}/process_info.json'.format(ticket_number)
        process_info = read_file(process_info_path, True)

        while process_info['status'] == 'in_progress':
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
                         "The resource with id, bad, does not exist for this user.")

        # Delete corresponding folder
        shutil.rmtree('mediafiles/downloads/{}'.format(ticket_number))