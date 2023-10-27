from typing import Literal

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.serializers import json_api
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.exceptions import ForestException


class ChartsCollectionResource(BaseCollectionResource):
    @ip_white_list
    async def dispatch(self, request: Request, method_name: Literal["add"]) -> Response:
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        if request.method == RequestMethod.POST:
            handle = self.handle_api_chart
        elif request.method == RequestMethod.GET:
            handle = self.handle_smart_chart
        else:
            msg = f"Method {request.method.value} is not allow for this url."
            ForestLogger.log("error", msg)
            return HttpResponseBuilder.build_client_error_response([ForestException(msg)])

        try:
            return HttpResponseBuilder.build_success_response(await handle(request_collection))
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

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
