from typing import TypedDict

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections import BoundCollection
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource
from forestadmin.agent_toolkit.resources.security.resources import Authentication
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.agent_toolkit.services.serializers.json_api import create_json_api_schema
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource


class Resources(TypedDict):
    authentication: Authentication
    crud: CrudResource
    crud_related: CrudRelatedResource


class Agent:
    def __init__(self, options: Options):
        self.options = options
        self.composite_datasource: Datasource[Collection] = Datasource()
        self.permission_service = PermissionService(
            {
                "env_secret": options["env_secret"],
                "forest_server_url": options["forest_server_url"],
                "is_production": options["is_production"],
                "permission_cache_duration": 60,
            }
        )

    @property
    def resources(self) -> Resources:
        return {
            "authentication": Authentication(self.options),
            "crud": CrudResource(self.composite_datasource, self.permission_service, self.options),
            "crud_related": CrudRelatedResource(self.composite_datasource, self.permission_service, self.options),
        }

    def add_datasource(self, datasource: Datasource[BoundCollection]):
        for collection in datasource.collections:
            self.composite_datasource.add_collection(collection)
            create_json_api_schema(collection)
