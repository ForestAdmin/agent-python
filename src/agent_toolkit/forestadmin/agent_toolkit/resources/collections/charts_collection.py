import sys

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.serializers import json_api
from forestadmin.agent_toolkit.utils.context import (
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_success_response,
)
from forestadmin.agent_toolkit.utils.id import unpack_id


class ChartsCollectionResource(BaseCollectionResource):
    async def dispatch(self, request: Request, method_name: Literal["add"]) -> Response:
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            return build_client_error_response([str(e)])

        if request.method == RequestMethod.POST:
            handle = self.handle_api_chart
        elif request.method == RequestMethod.GET:
            handle = self.handle_smart_chart
        else:
            return build_client_error_response([f"Method {request.method.value} is not allow for this url."])

        try:
            return build_success_response(await handle(request_collection))
        except Exception as exc:
            return build_client_error_response([str(exc)])

    @check_method(RequestMethod.POST)
    @authenticate
    async def handle_api_chart(self, request: RequestCollection) -> Response:
        ids = unpack_id(request.collection.schema, request.body.get("record_id") or request.query.get("record_id"))

        chart = await request.collection.render_chart(request.user, request.query["chart_name"], ids)
        return {"data": json_api.render_chart(chart)}

    @check_method(RequestMethod.GET)
    @authenticate
    async def handle_smart_chart(self, request: RequestCollection) -> Response:
        if request.query.get("record_id", None) is None:
            raise RequestCollectionException("Collection smart chart need a record id in the 'record_id' GET parameter")
        ids = unpack_id(request.collection.schema, str(request.query.get("record_id", "")))

        chart = await request.collection.render_chart(request.user, request.query["chart_name"], ids)
        return chart
