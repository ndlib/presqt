from presqt.osf.osf_classes.osf_core import OSFCore
from presqt.osf.osf_classes.osf_storage_folder import Storage


class Project(OSFCore):
    """
    Class that represents a project in the OSF API.
    """
    _types = ['nodes', 'registrations']

    def _update_attributes(self, project):
        """
        Add attributes to the class based on the JSON provided in the API call

        Parameters
        ----------
        project : dict
            Data dictionary returned from the json response to create the Project class instance.
        """
        if not project:
            return

        project = project['data']

        self._endpoint = project['links']['self']
        self.id = project['id']
        self._storages_url = project['relationships']['files']['links']['related']['href']

        attrs = project['attributes']
        self.title = attrs['title']
        self.date_created = attrs['date_created']
        self.date_modified = attrs['date_modified']
        self.description = attrs['description']

    def __str__(self):
        return '<project [{}]>'.format(self.id)

    def storage(self, provider='osfstorage'):
        """
        Return storage `provider` object.
        """
        stores_json = self._json(self._get(self._storages_url))

        for store in stores_json['data']:
            provides = store['attributes']['provider']
            if provides == provider:
                return Storage(store, self.session)

        raise RuntimeError("Project has no storage provider '{}'".format(provider))

    def storages(self):
        """
        Iterate over all storages for this project.
        """
        stores_json = self._json(self._get(self._storages_url))
        for store in stores_json['data']:
            yield Storage(store, self.session)

    def get_assets(self, assets):
        """
        Get all project assets. Return in the structure expected for the PresQT API.

        Parameters
        ----------
        assets : list
            Reference to the list of assets we want to add to.

        Returns
        -------
        List of project assets.
        """
        node_obj = {
            'kind': 'container',
            'kind_name': 'project',
            'id': self.id,
            'container': None,
            'title': self.title
        }
        assets.append(node_obj)

        for storage in self.storages():
            storage_obj = {
                'kind': 'container',
                'kind_name': 'storage',
                'id': storage.id,
                'container': self.id,
                'title': storage.name
            }
            assets.append(storage_obj)

            for asset in storage.get_assets_objects(storage.id):
                assets.append(asset)

        return assets