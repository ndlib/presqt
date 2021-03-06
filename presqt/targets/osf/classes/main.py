import json
import requests

from rest_framework import status

from presqt.targets.utilities import run_urls_async_with_pagination, get_duplicate_title
from presqt.utilities import (PresQTResponseException, PresQTInvalidTokenError,
                              get_dictionary_from_list, list_differences,
                              update_process_info, increment_process_info)
from presqt.targets.osf.classes.base import OSFBase
from presqt.targets.osf.classes.file import File
from presqt.targets.osf.classes.project import Project
from presqt.targets.osf.classes.storage_folder import Folder, Storage


class OSF(OSFBase):
    """
    Interact with the Open Science Framework.
    This is the main point of contact for interactions with the OSF.
    Use the methods of this class to find projects, login to the OSF, etc.
    """

    def __init__(self, token):
        super(OSF, self).__init__({})
        self.login(token)

    def login(self, token):
        """
        Login user for API calls.

        Parameters
        ----------
        token : str
            Token of the user performing the request.

        """
        self.session.token_auth({'Authorization': 'Bearer {}'.format(token)})
        # Verify that the token provided is a valid one.
        response = requests.get('https://api.osf.io/v2/users/me/',
                                headers={'Authorization': 'Bearer {}'.format(token)})
        if response.status_code == 401:
            raise PresQTInvalidTokenError(
                "Token is invalid. Response returned a 401 status code.")

    def project(self, project_id):
        """
        Get a project with the given project_id.

        Parameters
        ----------
        project_id : str
            id of the Project we want to fetch.

        Returns
        -------
        Instance of the desired Project.
        """
        url = self.session.build_url('nodes', project_id)
        return Project(self._json(self.get(url))['data'], self.session)

    def resource(self, resource_id):
        """
        Gets a file or folder with the given id.

        Parameters
        ----------
        resource_id : str
            id of the resource we want to fetch.

        Returns
        -------
        Instance of the desired resource (either Folder or File).
        """
        url = self.session.build_url('files', resource_id)
        response_json = self._json(self.get(url))['data']

        if response_json['attributes']['kind'] == 'file':
            return File(response_json, self.session)
        else:
            return Folder(response_json, self.session)

    def projects(self, url=None):
        """
        Fetch all projects for this user. Returns both top level projects and the full list of
        sub projects.
        """
        if not url:
            url = self.session.build_url('users', 'me', 'nodes')

        projects = []
        project_ids = []
        parent_project_ids = []
        # Since a user can collaborate on a subproject without having access to the parent project,
        # We need to get all top level projects who either have a parent_node of 'None' or whose
        # parent_node id isn't in our list of projects.
        for project_json in self._get_all_paginated_data(url):
            project = Project(project_json, self.session)
            projects.append(project)
            project_ids.append(project.id)
            parent_project_ids.append(project.parent_node_id)

        unique_project_ids = list_differences(parent_project_ids, project_ids)
        top_level_projects = [
            project for project in projects if project.parent_node_id in unique_project_ids]
        return projects, top_level_projects

    def get_resources(self, process_info_path, url=None):
        """
        Get all of the user's resources. To batch calls together asynchronously we will group calls
        together by projects, then storages, then each storage's resources.
        """
        resources = []
        all_projects, top_level_projects = self.projects(url)
        # Add all top level projects and subprojects to the resources list
        self.iter_project_hierarchy(all_projects, top_level_projects, resources)
        # Add all storages to the resource list
        user_storages_links = self.iter_project_storages(all_projects, resources)
        # Get initial resources for all storages
        all_storages_resources = run_urls_async_with_pagination(self, user_storages_links)

        # Add the total number of storages to the process info file.
        # This is necessary to keep track of the progress of the request.
        update_process_info(process_info_path, len(all_storages_resources), 'resource_collection', 'fetch')

        # Loop through the storage resources to either add them to the main resources list or
        # traverse further down the tree to get their children resources.
        for storage_resources in all_storages_resources:
            # Increment the number of files done in the process info file.
            increment_process_info(process_info_path, 'resource_collection', 'fetch')

            if storage_resources and storage_resources['data']: #TODO: First if check doing this to avoid private file errors look into it
                # Calculate the given resource's container_id
                parent_project_id = storage_resources['data'][0]['relationships']['node']['data']['id']
                parent_storage = storage_resources['data'][0]['attributes']['provider']
                container_id = '{}:{}'.format(parent_project_id, parent_storage)

                self.iter_resources_objects(storage_resources, resources, container_id)

        return resources

    def iter_project_hierarchy(self, all_projects, current_level_projects, resources):
        """
        Recursive function to add project data to the resources list.
        """
        # Keep track of every project's children links so we can call them asynchronously
        child_projects_links = []

        # Add each project to the resource list
        for project in current_level_projects:
            # It's possible for a project to be a subproject while the user does not have access to the
            # parent project. Check if the current project has a parent project owned by the user.
            for proj in all_projects:
                if proj.id == project.parent_node_id:
                    container_id = proj.id
                    break
            else:
                container_id = None

            resources.append({
                'kind': 'container',
                'kind_name': 'project',
                'id': project.id,
                'container': container_id,
                'title': project.title
            })
            child_projects_links.append(project.children_link)

        # Asynchronously get data for all child projects
        child_projects_data = run_urls_async_with_pagination(self, child_projects_links)

        # Create Project class instances for child projects
        children_projects = []
        for child_data in child_projects_data:
            for child in child_data['data']:
                child_project = Project(child, self.session)
                children_projects.append(child_project)

                # If the collection is part of a search result then the children projects haven't
                # been added to the main all_projects list yet. Add them in this case.
                for proj in all_projects:
                    if proj.id == child_project.id:
                        break
                else:
                    all_projects.append(child_project)

        # recursively call the iter_project_hierarchy for all child projects
        if children_projects:
            self.iter_project_hierarchy(all_projects, children_projects, resources)

    def iter_project_storages(self, projects, resources):
        """
        Function to add storage data to the resources list.
        """
        # Keep track of all storage file urls that need to be called.
        user_storages_links = []

        # Asynchronously get storage data for all projects
        storages = run_urls_async_with_pagination(
            self, [project._storages_url for project in projects])

        # Add each storage to the resource list
        for proj_storage in storages:
            for storage in proj_storage['data']:
                storage_obj = Storage(storage, self.session)
                resources.append({
                    'kind': 'container',
                    'kind_name': 'storage',
                    'id': storage_obj.id,
                    'container': storage_obj.node,
                    'title': storage_obj.title
                })
                user_storages_links.append(storage_obj._files_url)
        return user_storages_links

    def iter_resources_objects(self, container_resource, resources, container_id):
        """
        Recursive function to add resource data to the resources list.
        """
        folder_data = []
        for resource in container_resource['data']:
            kind = resource['attributes']['kind']

            if kind == 'file':
                file = File(resource, self.session)
                file_obj = {
                    'kind': file.kind,
                    'kind_name': file.kind_name,
                    'id': file.id,
                    'container': container_id,
                    'title': file.title
                }
                resources.append(file_obj)

            elif kind == 'folder':
                folder = Folder(resource, self.session)
                folder_obj = {
                    'kind': folder.kind,
                    'kind_name': folder.kind_name,
                    'id': folder.id,
                    'container': container_id,
                    'title': folder.title
                }
                resources.append(folder_obj)

                # Keep track of all folders' file urls that need to be called.
                folder_data.append({'url': folder._files_url,
                                    'id': folder.id,
                                    'path': folder.materialized_path})

        # Asynchronously call all folder file urls to get the folder's top level resources.
        all_folders_resources = run_urls_async_with_pagination(
            self, [folder_dict['url'] for folder_dict in folder_data])

        # For each folder, get it's container_id and resources
        for folder_resources in all_folders_resources:
            if folder_resources['data']:
                resource_attr = folder_resources['data'][0]['attributes']
                if resource_attr['kind'] == 'folder':
                    parent_path = resource_attr['materialized_path'][:-len(resource_attr['name'])-1]
                else:
                    parent_path = resource_attr['materialized_path'][:-len(resource_attr['name'])]
                # Find the corresponding parent_path in the folder_data list of dictionaries so we
                # can get the container id for this resource.
                container_id = get_dictionary_from_list(folder_data, 'path', parent_path)['id']

                self.iter_resources_objects(folder_resources, resources, container_id)

    def create_project(self, title):
        """-
        Create a project for this user.
        """
        titles = [project.title for project in self.projects()[1]]
        title = get_duplicate_title(title, titles, ' (PresQT*)')

        project_payload = {
            "data": {
                "type": "nodes",
                "attributes": {
                    "title": title,
                    "category": "project"
                }
            }
        }
        response = self.post(self.session.build_url('nodes'),
                             data=json.dumps(project_payload),
                             headers={'content-type': 'application/json'})

        if response.status_code == 201:
            return self.project(response.json()['data']['id'])
        else:
            raise PresQTResponseException(
                "Response has status code {} while creating project {}".format(response.status_code,
                                                                               title),
                status.HTTP_400_BAD_REQUEST)
