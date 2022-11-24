from typing import Any, Dict, List, Optional, Union

from forestadmin.agent_toolkit.resources.actions.requests import ActionRequest, RequestActionException
from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method
from forestadmin.agent_toolkit.resources.collections.filter import (
    build_filter,
    parse_condition_tree,
    parse_selection_ids,
)
from forestadmin.agent_toolkit.utils.context import (
    FileResponse,
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_json_response,
    build_success_response,
)
from forestadmin.agent_toolkit.utils.forest_schema.action_values import ForestValueConverter
from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerActionField
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class ActionResource(BaseCollectionResource):
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            request_collection = ActionRequest.from_request(request, self.datasource)
        except RequestActionException as e:
            return build_client_error_response([str(e)])
        return await method(request_collection)

    @check_method(RequestMethod.POST)
    @authenticate
    async def execute(self, request: ActionRequest) -> Union[FileResponse, Response]:
        if not request.body or not request.query:
            raise Exception
        filter = await self._get_records_selection(request)
        raw_data: Dict[str, Any] = request.body.get("data", {}).get("attributes", {}).get("values", {})  # type: ignore
        unsafe_data = ForestValueConverter.make_form_unsafe_data(raw_data)
        fields = await request.collection.get_form(request.action_name, raw_data, filter)
        data = ForestValueConverter.make_form_data(request.collection.datasource, unsafe_data, fields)
        result = await request.collection.execute(request.action_name, data, filter)
        if result["type"] == ResultBuilder.ERROR:
            return build_json_response(400, {"error": result["message"]})
        elif result["type"] == ResultBuilder.SUCCESS:
            key = "success"
            if result["format"] == "html":
                key = "html"
            return build_success_response({key: result["message"]})
        elif result["type"] == ResultBuilder.WEBHOOK:
            return build_success_response(
                {
                    "webhook": {
                        "url": result["url"],
                        "method": result["method"],
                        "headers": result["headers"],
                        "body": result["body"],
                    }
                }
            )
        elif result["type"] == ResultBuilder.FILE:
            return FileResponse(result["stream"], result["name"], result["mimeType"])

        elif result["type"] == ResultBuilder.REDIRECT:
            return build_success_response({"redirectTo": result["path"]})
        raise

    @check_method(RequestMethod.POST)
    @authenticate
    async def hook(self, request: ActionRequest) -> Response:
        if not request.body:
            raise Exception
        forest_fields: List[ForestServerActionField] = (
            request.body.get("data", {})  # type: ignore
            .get("attributes", {})  # type: ignore
            .get("fields", [])  # type: ignore
        )
        data: Optional[Dict[str, Any]] = None
        if forest_fields:
            data = ForestValueConverter.make_form_data_from_fields(request.collection.datasource, forest_fields)

        filter = await self._get_records_selection(request)
        fields = await request.collection.get_form(request.action_name, data, filter)

        return build_success_response(
            {
                "fields": [
                    await SchemaActionGenerator.build_field_schema(request.collection.datasource, field)
                    for field in fields
                ]
            }
        )

    async def _get_records_selection(self, request: ActionRequest) -> Filter:
        if not request.body:
            raise Exception()
        trees: List[ConditionTree] = []
        selection_ids, exclude_ids = parse_selection_ids(request)
        selected_ids = ConditionTreeFactory.match_ids(request.collection.schema, selection_ids)
        if exclude_ids:
            selected_ids = selected_ids.inverse()

        if selected_ids != ConditionTreeBranch(Aggregator.OR, []):
            trees.append(selected_ids)
        query_param_condition_tree = parse_condition_tree(request)
        if query_param_condition_tree:
            trees.append(query_param_condition_tree)
        scope_tree = await self.permission.get_scope(request)
        if scope_tree:
            trees.append(scope_tree)

        if trees:
            condition_tree = ConditionTreeFactory.intersect(trees)
        else:
            condition_tree = None
        filter = build_filter(request, condition_tree)
        attributes: Dict[str, Any] = request.body.get("data", {}).get("attributes", {})
        if "parent_association_name" in attributes:
            pass
        return filter
