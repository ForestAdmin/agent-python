from typing import Any, Dict, List, Literal, Union
from uuid import uuid4

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.resources.context_variable_injector_mixin import ContextVariableInjectorResourceMixin
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.agent_toolkit.utils.sql_query_checker import SqlQueryChecker
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.exceptions import BusinessError, ForbiddenError, UnprocessableError, ValidationError
from forestadmin.datasource_toolkit.interfaces.chart import (
    Chart,
    DistributionChart,
    LeaderboardChart,
    ObjectiveChart,
    TimeBasedChart,
    ValueChart,
)
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
        except ForbiddenError as exc:
            return HttpResponseBuilder.build_client_error_response([exc])
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_native_query(self, request: Request) -> Response:
        await self.permission.can_chart(request)
        assert request.body is not None
        if request.body.get("connectionName") is None:
            raise BusinessError("Missing native query connection attribute")
        if "query" not in request.body:
            raise BusinessError("Missing 'query' in parameter.")
        if request.body.get("type") not in ["Line", "Objective", "Leaderboard", "Pie", "Value"]:
            raise ValidationError(f"Unknown chart type '{request.body.get('type')}'.")

        SqlQueryChecker.check_query(request.body["query"])
        variables = await self.inject_and_get_context_variables_in_live_query_chart(request)
        native_query_results = await self.composite_datasource.execute_native_query(
            request.body["connectionName"], request.body["query"], variables
        )

        chart_result: Chart
        if request.body["type"] == "Line":
            chart_result = self._handle_line_chart(native_query_results)
        elif request.body["type"] == "Objective":
            chart_result = self._handle_objective_chart(native_query_results)
        elif request.body["type"] == "Leaderboard":
            chart_result = self._handle_leaderboard_chart(native_query_results)
        elif request.body["type"] == "Pie":
            chart_result = self._handle_pie_chart(native_query_results)
        elif request.body["type"] == "Value":
            chart_result = self._handle_value_chart(native_query_results)

        return HttpResponseBuilder.build_success_response(
            {
                "data": {
                    "id": str(uuid4()),
                    "type": "stats",
                    "attributes": {
                        "value": chart_result,  # type:ignore
                    },
                }
            }
        )

    def _handle_line_chart(self, native_query_results: List[Dict[str, Any]]) -> TimeBasedChart:
        if len(native_query_results) >= 1:
            if "key" not in native_query_results[0] or "value" not in native_query_results[0]:
                raise UnprocessableError("Native query for 'Line' chart must return 'key' and 'value' fields.")

        return [{"label": res["key"], "values": {"value": res["value"]}} for res in native_query_results]

    def _handle_objective_chart(self, native_query_results: List[Dict[str, Any]]) -> ObjectiveChart:
        if len(native_query_results) == 1:
            if "value" not in native_query_results[0] or "objective" not in native_query_results[0]:
                raise UnprocessableError(
                    "Native query for 'Objective' chart must return 'value' and 'objective' fields."
                )
        else:
            raise UnprocessableError("Native query for 'Objective' chart must return only one row.")

        return {
            "value": native_query_results[0]["value"],
            "objective": native_query_results[0]["objective"],
        }

    def _handle_leaderboard_chart(self, native_query_results: List[Dict[str, Any]]) -> LeaderboardChart:
        if len(native_query_results) >= 1:
            if "key" not in native_query_results[0] or "value" not in native_query_results[0]:
                raise UnprocessableError("Native query for 'Leaderboard' chart must return 'key' and 'value' fields.")

        return [{"key": res["key"], "value": res["value"]} for res in native_query_results]

    def _handle_pie_chart(self, native_query_results: List[Dict[str, Any]]) -> DistributionChart:
        if len(native_query_results) >= 1:
            if "key" not in native_query_results[0] or "value" not in native_query_results[0]:
                raise UnprocessableError("Native query for 'Pie' chart must return 'key' and 'value' fields.")

        return [{"key": res["key"], "value": res["value"]} for res in native_query_results]

    def _handle_value_chart(self, native_query_results: List[Dict[str, Any]]) -> ValueChart:
        if len(native_query_results) == 1:
            if "value" not in native_query_results[0]:
                raise UnprocessableError("Native query for 'Value' chart must return 'value' field.")
        else:
            raise UnprocessableError("Native query for 'Value' chart must return only one row.")

        ret = {"countCurrent": native_query_results[0]["value"]}
        if "previous" in native_query_results[0]:
            ret["countPrevious"] = native_query_results[0]["previous"]
        return ret  # type:ignore
