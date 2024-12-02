from typing import Literal, Union
from uuid import uuid4

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.resources.context_variable_injector_mixin import ContextVariableInjectorResourceMixin
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.exceptions import BusinessError
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, Datasource

DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


LiteralMethod = Literal["native_query"]


class NativeQueryResource(BaseCollectionResource, ContextVariableInjectorResourceMixin):
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
            return await self.handle_native_query(request)  # type:ignore
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_native_query(self, request: Request) -> Response:
        await self.permission.can_chart(request)
        assert request.body is not None
        if "connectionName" not in request.body:
            raise BusinessError("Missing 'connectionName' in parameter.")
        if "query" not in request.body:
            raise BusinessError("Missing 'query' in parameter.")

        variables = await self.inject_and_get_context_variables_in_live_query_chart(request)
        return HttpResponseBuilder.build_success_response(
            {
                "data": {
                    "id": str(uuid4()),
                    "type": "stats",
                    "attributes": {
                        "value": await self.composite_datasource.execute_native_query(
                            request.body["connectionName"], request.body["query"], variables
                        ),
                    },
                }
            }
        )
