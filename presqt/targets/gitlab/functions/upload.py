import base64
import os

import requests
from rest_framework import status

from presqt.targets.gitlab.utilities import gitlab_paginated_data
from presqt.targets.gitlab.utilities.validation_check import validation_check
from presqt.targets.utilities import get_duplicate_title
from presqt.utilities import PresQTResponseException


def gitlab_upload_resource(token, resource_id, resource_main_dir, hash_algorithm, file_duplicate_action):
    """
    Upload the files found in the resource_main_dir to the target.

    Parameters
    ----------
    token : str
        User's token.
    resource_id : str
        ID of the resource requested.
    resource_main_dir : str
        Path to the main directory for the resources to be uploaded.
    hash_algorithm : str
        Hash algorithm we are using to check for fixity.
    file_duplicate_action : str
        The action to take when a duplicate file is found

    Returns
    -------
    Dictionary with the following keys: values
        'resources_ignored' : Array of string file paths of files that were ignored when
        uploading the resource. Path should have the same base as resource_main_dir.
                                Example:
                                    ['path/to/ignored/file.pg', 'another/ignored/file.jpg']

        'resources_updated' : Array of string file paths of files that were updated when
         uploading the resource. Path should have the same base as resource_main_dir.
                                 Example:
                                    ['path/to/updated/file.jpg']
        'action_metadata': Dictionary containing action metadata. Must be in the following format:
                            {
                                'destinationUsername': 'some_username'
                            }
        'file_metadata_list': List of dictionaries for each file that contains metadata
                              and hash info. Must be in the following format:
                                {
                                    "actionRootPath": '/path/on/disk',
                                    "destinationPath": '/path/on/target/destination',
                                    "title": 'file_title',
                                    "destinationHash": {'hash_algorithm': 'the_hash'}}
                                }
        'project_id': ID of the parent project for this upload. Needed for metadata upload.
    """
    base_url = "https://gitlab.com/api/v4/"

# Uploading to an existing GitLab repository is not allowed
    if resource_id:
        raise PresQTResponseException("Can't upload to an existing GitLab repository.",
                                      status.HTTP_400_BAD_REQUEST)

    try:
        headers, user_id = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    #*** CREATE PROJECT ***#
    # Create a new project with the name being the top level directory's name.
    os_path = next(os.walk(resource_main_dir))

    # Check if a project with this name exists for this user
    project_title = os_path[1][0]

    titles = [data['name'] for data in gitlab_paginated_data(headers, user_id)]
    title = get_duplicate_title(project_title, titles, '-PresQT*-')

    response = requests.post('{}projects?name={}&visibility=public'.format(base_url, title), headers=headers)

    if response.status_code == 201:
        project_id = response.json()['id']
    else:
        raise PresQTResponseException(
            "Response has status code {} while creating project {}".format(
                response.status_code, project_title), status.HTTP_400_BAD_REQUEST)

    #*** UPLOAD FILES ***#
    # Upload files to project's repository
    username = requests.get("https://gitlab.com/api/v4/user", headers=headers).json()['username']
    action_metadata = {"destinationUsername": username}
    resources_ignored = []
    file_metadata_list = []
    base_repo_path = "{}projects/{}/repository/files/".format(base_url, project_id)
    for path, subdirs, files in os.walk(resource_main_dir):
        if not subdirs and not files:
            resources_ignored.append(path)
        for name in files:
            # Strip server directories from file path
            relative_file_path = os.path.join(path.partition('/data/{}/'.format(project_title))[2],
                                              name)

            # Extract and encode the file bytes in the way expected by GitLab.
            file_bytes = open(os.path.join(path, name), 'rb').read()
            encoded_file = base64.b64encode(file_bytes)

            # A relative path to the file is what is added to the GitLab POST address
            encoded_file_path = relative_file_path.replace('/', '%2F').replace('.', '%2E')

            request_data = {"branch": "master",
                            "commit_message": "PresQT Upload",
                            "encoding": "base64",
                            "content": encoded_file}

            requests.post("{}{}".format(
                base_repo_path, encoded_file_path), headers=headers, data=request_data)

            # Get the file hash
            file_json = requests.get("{}{}?ref=master".format(base_repo_path, encoded_file_path),
                                     headers=headers)

            file_metadata_list.append({
                "actionRootPath": os.path.join(path, name),
                "destinationPath": os.path.join(path.partition('/data/')[2], name),
                "title": name,
                "destinationHash": file_json.json()['content_sha256']
            })

    return {
        'resources_ignored': resources_ignored,
        'resources_updated': [],
        'action_metadata': action_metadata,
        'file_metadata_list': file_metadata_list,
        'project_id': project_id
    }