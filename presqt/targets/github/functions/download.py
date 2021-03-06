import asyncio

import aiohttp
import requests

from rest_framework import status

from presqt.targets.github.utilities import (
    validation_check, download_content, download_directory, download_file, extra_metadata_helper)
from presqt.utilities import (PresQTResponseException, get_dictionary_from_list,
                              update_process_info, increment_process_info, update_process_info_message)


async def async_get(url, session, header, process_info_path, action):
    """
    Coroutine that uses aiohttp to make a GET request. This is the method that will be called
    asynchronously with other GETs.

    Parameters
    ----------
    url: str
        URL to call
    session: ClientSession object
        aiohttp ClientSession Object
    header: str
        Header for request
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

    Returns
    -------
    Response JSON
    """
    async with session.get(url, headers=header) as response:
        assert response.status == 200
        content = await response.read()
        # Increment the number of files done in the process info file.
        increment_process_info(process_info_path, action, 'download')
        return {'url': url, 'binary_content': content}


async def async_main(url_list, header, process_info_path, action):
    """
    Main coroutine method that will gather the url calls to be made and will make them
    asynchronously.

    Parameters
    ----------
    url_list: list
        List of urls to call
    header: str
        Header for request
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed

    Returns
    -------
    List of data brought back from each coroutine called.
    """
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[async_get(url, session, header, process_info_path, action) for url in url_list])


def github_download_resource(token, resource_id, process_info_path, action):
    """
    Fetch the requested resource from GitHub along with its hash information.

    Parameters
    ----------
    token : str
        User's GitHub token
    resource_id : str
        ID of the resource requested
    process_info_path: str
        Path to the process info file that keeps track of the action's progress
    action: str
        The action being performed


    Returns
    -------
    Dictionary with the following keys: values
        'resources': List of dictionary objects that each hold a file and its information.
                     Dictionary must be in the following format:
                         {
                            'file': binary_file,
                            'hashes': {'hash_algorithm': 'the_hash'},
                            'title': 'file.jpg',
                            'path': '/path/to/file',
                            'source_path: '/full/path/to/file',
                            'extra_metadata': {'any': 'extra'}
                         }
        'empty_containers: List of string paths representing empty containers that must be written.
                              Example: ['empty/folder/to/write/', 'another/empty/folder/]
        'action_metadata': Dictionary containing action metadata. Must be in the following format:
                              {
                              'sourceUsername': 'some_username',
                              }
    """
    try:
        header, username = validation_check(token)
    except PresQTResponseException:
        raise PresQTResponseException("Token is invalid. Response returned a 401 status code.",
                                      status.HTTP_401_UNAUTHORIZED)

    extra_metadata = {}
    # Without a colon, we know this is a top level repo
    if ':' not in resource_id:
        project_url = 'https://api.github.com/repositories/{}'.format(resource_id)
        response = requests.get(project_url, headers=header)

        if response.status_code != 200:
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)
        data = response.json()

        repo_name = data['name']
        # Strip off the unnecessary {+path} that's included in the url
        # Example: https://api.github.com/repos/eggyboi/djangoblog/contents/{+path} becomes
        # https://api.github.com/repos/eggyboi/djangoblog/contents
        contents_url = data['contents_url'].partition('/{+path}')[0]

        files, empty_containers, action_metadata = download_content(
            username, contents_url, header, repo_name, [])
        file_urls = [file['file'] for file in files]

        update_process_info_message(process_info_path, action, 'Downloading files from GitHub...')
        # Add the total number of repository to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, len(file_urls), action, 'download')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        download_data = loop.run_until_complete(
            async_main(file_urls, header, process_info_path, action))

        # Go through the file dictionaries and replace the file path with the binary_content
        for file in files:
            file['file'] = get_dictionary_from_list(
                download_data, 'url', file['file'])['binary_content']

        extra_metadata = extra_metadata_helper(response.json(), repo_name, header)

    # If there is a colon in the resource id, the resource could be a directory or a file
    else:
        partitioned_id = resource_id.partition(':')
        repo_id = partitioned_id[0]
        path_to_file = partitioned_id[2].replace(
            '%2F', '/').replace('%2E', '.').replace('%252F', '/').replace('%252E', '.')

        # Get initial repo data for the resource requested
        repo_url = 'https://api.github.com/repositories/{}'.format(repo_id)
        response = requests.get(repo_url, headers=header)

        if response.status_code != 200:
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)
        repo_data = response.json()

        # Get the contents of the requested resource
        repo_full_name = repo_data['full_name']
        resource_url = 'https://api.github.com/repos/{}/contents/{}'.format(repo_full_name,
                                                                            path_to_file)
        resource_response = requests.get(resource_url, headers=header)
        resource_data = resource_response.json()
        if resource_response.status_code == 403:
            # 403 most likely means the blob contents were too big so we have to attempt to
            # get the file contents a different method
            trees_url = '{}/master?recursive=1'.format(repo_data['trees_url'][:-6])
            trees_response = requests.get(trees_url, headers=header)
            for tree in trees_response.json()['tree']:
                if path_to_file == tree['path']:
                    file_sha = tree['sha']
            git_blob_url = 'https://api.github.com/repos/{}/git/blobs/{}'.format(
                repo_data['full_name'], file_sha)
            file_get = requests.get(git_blob_url, headers=header)
            resource_data = file_get.json()
            resource_data['name'] = path_to_file.rpartition('/')[2]
            resource_data['path'] = path_to_file.rpartition('/')
            resource_data['type'] = 'file'
        elif resource_response.status_code != 200:
            raise PresQTResponseException(
                'The resource with id, {}, does not exist for this user.'.format(resource_id),
                status.HTTP_404_NOT_FOUND)

        # If the resource to get is a folder
        if isinstance(resource_data, list):
            update_process_info_message(process_info_path, action,
                                        'Downloading files from GitHub...')
            files = download_directory(header, path_to_file, repo_data, process_info_path, action)
        # If the resource to get is a file
        elif resource_data['type'] == 'file':
            update_process_info_message(process_info_path, action,
                                        'Downloading files from GitHub...')
            update_process_info(process_info_path, 1, action, 'download')
            files = download_file(repo_data, resource_data, process_info_path, action)

        empty_containers = []
        action_metadata = {"sourceUsername": username}

    return {
        'resources': files,
        'empty_containers': empty_containers,
        'action_metadata': action_metadata,
        'extra_metadata': extra_metadata
    }
