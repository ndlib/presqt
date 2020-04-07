from presqt.targets.github.functions.fetch import github_fetch_resources, github_fetch_resource
from presqt.targets.github.functions.download import github_download_resource
from presqt.targets.github.functions.upload import github_upload_resource
from presqt.targets.github.functions.upload_metadata import github_upload_metadata

from presqt.targets.curate_nd.functions.fetch import (
    curate_nd_fetch_resources, curate_nd_fetch_resource)
from presqt.targets.curate_nd.functions.download import curate_nd_download_resource
from presqt.targets.gitlab.functions.fetch import gitlab_fetch_resources, gitlab_fetch_resource

from presqt.targets.osf.functions.fetch import osf_fetch_resources, osf_fetch_resource
from presqt.targets.osf.functions.download import osf_download_resource
from presqt.targets.osf.functions.upload import osf_upload_resource
from presqt.targets.osf.functions.upload_metadata import osf_upload_metadata

from presqt.targets.zenodo.functions.fetch import zenodo_fetch_resources, zenodo_fetch_resource
from presqt.targets.zenodo.functions.download import zenodo_download_resource
from presqt.targets.zenodo.functions.upload import zenodo_upload_resource
from presqt.targets.zenodo.functions.upload_metadata import zenodo_upload_metadata


class FunctionRouter(object):
    """
    This class acts as a router to allow dynamic function calls based on a given variable.

    Each attribute links to a function. Naming conventions are important. They must match the keys
    we keep in the target.json config file. They are as follows:

    Target Resources Collection:
        {target_name}_resource_collection

    Target Resource Detail:
        {target_name}_resource_detail

    Target Resource Download:
        {target_name}_resource_download

    Target Resource Upload:
        {target_name}_resource_upload

    Target Resource FTS Metadata Upload:
        {target_name}_metadata_upload

    """
    @classmethod
    def get_function(cls, target_name, action):
        """
        Extracts the getattr() function call to this class method so the code using this class
        is easier to work with.
        """
        return getattr(cls, '{}_{}'.format(target_name, action))

    osf_resource_collection = osf_fetch_resources
    osf_resource_detail = osf_fetch_resource
    osf_resource_download = osf_download_resource
    osf_resource_upload = osf_upload_resource
    osf_metadata_upload = osf_upload_metadata

    curate_nd_resource_collection = curate_nd_fetch_resources
    curate_nd_resource_detail = curate_nd_fetch_resource
    curate_nd_resource_download = curate_nd_download_resource

    github_resource_collection = github_fetch_resources
    github_resource_detail = github_fetch_resource
    github_resource_download = github_download_resource
    github_resource_upload = github_upload_resource
    github_metadata_upload = github_upload_metadata

    zenodo_resource_collection = zenodo_fetch_resources
    zenodo_resource_detail = zenodo_fetch_resource
    zenodo_resource_download = zenodo_download_resource
    zenodo_resource_upload = zenodo_upload_resource
    zenodo_metadata_upload = zenodo_upload_metadata

    gitlab_resource_collection = gitlab_fetch_resources
    gitlab_resource_detail = gitlab_fetch_resource

