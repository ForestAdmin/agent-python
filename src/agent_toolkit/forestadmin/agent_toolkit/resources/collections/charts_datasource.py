import sys
from typing import Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method
from forestadmin.agent_toolkit.services.serializers import json_api
from forestadmin.agent_toolkit.utils.context import (
    FileResponse,
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_success_response,
)


class ChartsDatasourceResource(BaseCollectionResource):
    async def dispatch(self, request: Request, method_name: Literal["add"]) -> Union[Response, FileResponse]:
        if request.method.value == "POST":
            handle = self.handle_api_chart
        elif request.method.value == "GET":
            handle = self.handle_smart_chart
        else:
            return build_client_error_response([f"Method {request.method.value} is not allow for this url."])

        try:
            return build_success_response(await handle(request))
        except Exception as exc:
            return build_client_error_response([str(exc)])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_api_chart(self, request: Request) -> Response:
        chart = await self.datasource.render_chart(request.user, request.query["chart_name"])
        return {"data": json_api.render_chart(chart)}

    @check_method(RequestMethod.GET)
    @authenticate
    async def handle_smart_chart(self, request: Request) -> Response:
        return await self.datasource.render_chart(request.user, request.query["chart_name"])
