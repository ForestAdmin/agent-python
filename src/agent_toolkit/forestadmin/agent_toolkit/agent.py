import copy
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.options import DEFAULT_OPTIONS, Options
from forestadmin.agent_toolkit.resources.actions.resources import ActionResource
from forestadmin.agent_toolkit.resources.collections import BoundCollection
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource
from forestadmin.agent_toolkit.resources.collections.stats import StatsResource
from forestadmin.agent_toolkit.resources.security.resources import Authentication
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.agent_toolkit.services.serializers.json_api import create_json_api_schema
from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource


class Resources(TypedDict):
    authentication: Authentication
    crud: CrudResource
    crud_related: CrudRelatedResource
    stats: StatsResource
    actions: ActionResource


class Agent:
    __IS_INITIALIZED: bool = False
    META: AgentMeta = None

    def __init__(self, options: Options):
        self.options = copy.copy(DEFAULT_OPTIONS)
        self.options.update(options)
        self.customizer: DatasourceCustomizer = DatasourceCustomizer()
        self._resources = None

        self._permission_service = PermissionService(
            {
                "env_secret": self.options["env_secret"],
                "forest_server_url": self.options["forest_server_url"],
                "is_production": self.options["is_production"],
                "permission_cache_duration": 60,
            }
        )

    def __mk_resources(self):
        self._resources: Resources = {
            "authentication": Authentication(self.options),
            "crud": CrudResource(self.customizer.stack.datasource, self._permission_service, self.options),
            "crud_related": CrudRelatedResource(
                self.customizer.stack.datasource, self._permission_service, self.options
            ),
            "stats": StatsResource(self.customizer.stack.datasource, self._permission_service, self.options),
            "actions": ActionResource(self.customizer.stack.datasource, self._permission_service, self.options),
        }

    @property
    def resources(self) -> Resources:
        if self._resources is None:
            self.__mk_resources()
        return self._resources

    def add_datasource(self, datasource: Datasource[BoundCollection]):
        self.customizer.add_datasource(datasource, {})
        self._resources = None

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        return self.customizer.customize_collection(collection_name)

    @property
    def meta(self) -> AgentMeta:
        meta = getattr(self, "META", None)
        if meta is None:
            raise AgentToolkitException("The agent subclass should set the META attribute")
        return meta

    async def start(self):
        if Agent.__IS_INITIALIZED is True:
            return

        for collection in self.customizer.stack.datasource.collections:
            create_json_api_schema(collection)

        api_map = await SchemaEmitter.get_serialized_schema(self.options, self.customizer.stack.datasource, self.meta)

        await ForestHttpApi.send_schema(self.options, api_map)
        Agent.__IS_INITIALIZED = True
