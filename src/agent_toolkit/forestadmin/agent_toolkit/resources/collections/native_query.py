from typing import Literal, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, Datasource

DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


LiteralMethod = Literal["native_query"]


class NativeQueryResource(BaseCollectionResource):
    def __init__(
        self,
        composite_datasource: CompositeDatasource,
        datasource: DatasourceAlias,
        permission: PermissionService,
        ip_white_list_service: IpWhiteListService,
        options: Options,
    ):
        super().__init__(datasource, permission, ip_white_list_service, options)
        self.composite_datasource: CompositeDatasource = composite_datasource

    @ip_white_list
    async def dispatch(self, request: Request, method_name: Literal["native_query"]) -> Response:
        try:
            return HttpResponseBuilder.build_success_response(await self.handle_native_query(request))
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_native_query(self, request: Request) -> Response:
        # TODO: permission check
        # TODO: context variable injector
        ds = self.composite_datasource.get_datasource(request.body["datasource"])
        return await ds.execute_native_query(request.body["native_query"])
