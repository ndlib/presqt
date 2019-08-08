from rest_framework.response import Response
from rest_framework.views import APIView

from presqt.api_v1.serializers.resource import ResourcesSerializer
from presqt.api_v1.utilities import target_validation, FunctionRouter, get_source_token
from presqt.api_v1.views.resource.base_resource import BaseResource
from presqt.utilities import PresQTValidationError, PresQTResponseException


class ResourceCollection(BaseResource):
    """
    **Supported HTTP Methods**

    * GET:
        - Retrieve a summary of all resources for the given Target that a user has access to.
    * POST
        -  Upload a top level resource for a user.
    """
    required_scopes = ['read']

    def get(self, request, target_name):
        """
        Retrieve all Resources.

        Parameters
        ----------
        target_name : str
            The string name of the Target resource to retrieve.

        Returns
        -------
        200 : OK
        A list-like JSON representation of all resources for the given Target and token.
        [
            {
                "kind": "container",
                "kind_name": "folder",
                "id": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc",
                "container": "None",
                "title": "Folder Name",
                "detail": "http://localhost/api_v1/targets/osf/resources/a02d7b96-a4a9-4521-9913-e3cc68f4d9dc"
            },
            {
                "kind": "item",
                "kind_name": "file",
                "id": "5b305f1b-0da6-4a1a-9861-3bb159d94c96",
                "container": "a02d7b96-a4a9-4521-9913-e3cc68f4d9dc",
                "title": "file.jpg",
                "detail": "http://localhost/api_v1/targets/osf/resources/5b305f1b-0da6-4a1a-9861-3bb159d94c96"
            }
        ]

        400: Bad Request
        {
            "error": "'new_target' does not support the action 'resource_collection'."
        }
        or
        {
            "error": "'presqt-source-token' missing in the request headers."
        }

        401: Unauthorized
        {
            "error": "Token is invalid. Response returned a 401 status code.""
        }

        404: Not Found
        {
            "error": "'bad_target' is not a valid Target name."
        }
        """
        action = 'resource_collection'

        # Perform token, target, and action validation
        try:
            token = get_source_token(request)
            target_validation(target_name, action)
        except PresQTValidationError as e:
            return Response(data={'error': e.data}, status=e.status_code)

        # Fetch the proper function to call
        func = FunctionRouter.get_function(target_name, action)

        # Fetch the target's resources
        try:
            resources = func(token)
        except PresQTResponseException as e:
            # Catch any errors that happen within the target fetch
            return Response(data={'error': e.data}, status=e.status_code)

        serializer = ResourcesSerializer(instance=resources, many=True, context={
                                         'target_name': target_name,
                                         'request': request})

        return Response(serializer.data)
