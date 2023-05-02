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
from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection


class Resources(TypedDict):
    authentication: Authentication
    crud: CrudResource
    crud_related: CrudRelatedResource
    stats: StatsResource
    actions: ActionResource


class Agent:
    META: AgentMeta = None

    def __init__(self, options: Options):
        self.options = copy.copy(DEFAULT_OPTIONS)
        self.options.update(options)
        self.customizer: DatasourceCustomizer = DatasourceCustomizer()

        self.permission_service = PermissionService(
            {
                "env_secret": self.options["env_secret"],
                "forest_server_url": self.options["forest_server_url"],
                "is_production": self.options["is_production"],
                "permission_cache_duration": 60,
            }
        )

    @property
    def resources(self) -> Resources:
        return {
            "authentication": Authentication(self.options),
            "crud": CrudResource(self.customizer.composite_datasource, self.permission_service, self.options),
            "crud_related": CrudRelatedResource(
                self.customizer.composite_datasource, self.permission_service, self.options
            ),
            "stats": StatsResource(self.customizer.composite_datasource, self.permission_service, self.options),
            "actions": ActionResource(self.customizer.composite_datasource, self.permission_service, self.options),
        }

    def add_datasource(self, datasource: Datasource[BoundCollection]):
        self.customizer.add_datasource(datasource)

    def customize_collection(self, collection_name: str) -> CustomizedCollection:
        return self.customizer.customize_collection(collection_name)

    @property
    def meta(self) -> AgentMeta:
        try:
            return getattr(self, "META")
        except AttributeError:
            raise AgentToolkitException("The agent subclass should set the META attribute")

    async def start(self):
        api_map = await SchemaEmitter.get_serialized_schema(
            self.options, self.customizer.composite_datasource, self.meta
        )

        await ForestHttpApi.send_schema(self.options, api_map)
