import copy
from typing import Dict, List, Optional, TypedDict, Union

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import DEFAULT_OPTIONS, Options
from forestadmin.agent_toolkit.resources.actions.resources import ActionResource
from forestadmin.agent_toolkit.resources.collections.charts_collection import ChartsCollectionResource
from forestadmin.agent_toolkit.resources.collections.charts_datasource import ChartsDatasourceResource
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource
from forestadmin.agent_toolkit.resources.collections.stats import StatsResource
from forestadmin.agent_toolkit.resources.security.resources import Authentication
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.services.permissions.sse_cache_invalidation import SSECacheInvalidation
from forestadmin.agent_toolkit.services.serializers.json_api import create_json_api_schema
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder
from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.types import DataSourceOptions
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.types import DataSourceChartDefinition
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection
from typing_extensions import Self


class Resources(TypedDict):
    authentication: Authentication
    crud: CrudResource
    crud_related: CrudRelatedResource
    stats: StatsResource
    actions: ActionResource
    collection_charts: ChartsCollectionResource
    datasource_charts: ChartsDatasourceResource


class Agent:
    __IS_INITIALIZED: bool = False
    META: AgentMeta = None

    def __init__(self, options: Options):
        self.options = copy.copy(DEFAULT_OPTIONS)
        self.options.update({k: v for k, v in options.items() if v is not None})
        if self.options["instant_cache_refresh"] is None:
            self.options["instant_cache_refresh"] = self.options["is_production"]
        self.customizer: DatasourceCustomizer = DatasourceCustomizer()
        self._resources = None

        ForestLogger.setup_logger(self.options["logger_level"], self.options["logger"])

        if "customize_error_message" in self.options:
            HttpResponseBuilder.setup_error_message_customizer(self.options["customize_error_message"])

        service_options = {
            "env_secret": self.options["env_secret"],
            "forest_server_url": self.options["forest_server_url"],
            "is_production": self.options["is_production"],
            "permission_cache_duration": self.options["permissions_cache_duration_in_seconds"],
            "prefix": self.options["prefix"],
        }
        self._permission_service = PermissionService(service_options)
        self._ip_white_list_service = IpWhiteListService(service_options)

        # TODO: add ip_white_list_service to sse cache invalidation thread when server implement it
        self._sse_thread = SSECacheInvalidation(self._permission_service, self.options)

    def __del__(self):
        if hasattr(self, "_sse_thread") and self._sse_thread.is_alive():
            self._sse_thread.stop()

    async def __mk_resources(self):
        self._resources: Resources = {
            "authentication": Authentication(self._ip_white_list_service, self.options),
            "crud": CrudResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
            "crud_related": CrudRelatedResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
            "stats": StatsResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
            "actions": ActionResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
            "collection_charts": ChartsCollectionResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
            "datasource_charts": ChartsDatasourceResource(
                await self.customizer.get_datasource(),
                self._permission_service,
                self._ip_white_list_service,
                self.options,
            ),
        }

    async def get_resources(self):
        if self._resources is None:
            await self.__mk_resources()
        return self._resources

    def add_datasource(self, datasource: Datasource[BoundCollection], options: Optional[DataSourceOptions] = None):
        if options is None:
            options = {}
        self.customizer.add_datasource(datasource, options)
        self._resources = None

    def use(self, plugin: type, options: Optional[Dict] = {}) -> Self:
        self.customizer.use(plugin, options)
        return self

    def customize_collection(self, collection_name: str) -> CollectionCustomizer:
        return self.customizer.customize_collection(collection_name)

    def remove_collections(self, names: Union[str, List[str]]):
        return self.customizer.remove_collections(names)

    def add_chart(self, name: str, definition: DataSourceChartDefinition):
        return self.customizer.add_chart(name, definition)

    @property
    def meta(self) -> AgentMeta:
        meta = getattr(self, "META", None)
        if meta is None:
            raise AgentToolkitException("The agent subclass should set the META attribute")
        return meta

    async def start(self):
        if Agent.__IS_INITIALIZED is True:
            ForestLogger.log("debug", "Agent already started.")
            return
        ForestLogger.log("debug", "Starting agent")

        if self.options["skip_schema_update"] is False:
            try:
                api_map = await SchemaEmitter.get_serialized_schema(
                    self.options, await self.customizer.get_datasource(), self.meta
                )
            except Exception:
                ForestLogger.log("exception", "Error generating forest schema")

            try:
                await ForestHttpApi.send_schema(self.options, api_map)
            except Exception:
                ForestLogger.log("warning", "Cannot send the apimap to Forest. Are you online?")
        else:
            ForestLogger.log("warning", 'Schema update was skipped (caused by options["skip_schema_update"]=True)')

        for collection in (await self.customizer.get_datasource()).collections:
            create_json_api_schema(collection)

        if self.options["instant_cache_refresh"]:
            self._sse_thread.start()

        ForestLogger.log("info", "Agent started")
        Agent.__IS_INITIALIZED = True
