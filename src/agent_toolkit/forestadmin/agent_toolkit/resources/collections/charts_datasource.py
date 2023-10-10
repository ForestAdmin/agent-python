from typing import Literal, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.services.serializers import json_api
from forestadmin.agent_toolkit.utils.context import FileResponse, HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.datasource_toolkit.exceptions import ForestException


class ChartsDatasourceResource(BaseCollectionResource):
    @ip_white_list
    async def dispatch(self, request: Request, method_name: Literal["add"]) -> Union[Response, FileResponse]:
        if request.method.value == "POST":
            handle = self.handle_api_chart
        elif request.method.value == "GET":
            handle = self.handle_smart_chart
        else:
            msg = f"Method {request.method.value} is not allow for this url."
            ForestLogger.log("error", msg)
            return HttpResponseBuilder.build_client_error_response([ForestException(msg)])

        try:
            return HttpResponseBuilder.build_success_response(await handle(request))
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_api_chart(self, request: Request) -> Response:
        chart = await self.datasource.render_chart(request.user, request.query["chart_name"])
        return {"data": json_api.render_chart(chart)}

    @check_method(RequestMethod.GET)
    @authenticate
    async def handle_smart_chart(self, request: Request) -> Response:
        return await self.datasource.render_chart(request.user, request.query["chart_name"])
