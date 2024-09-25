from typing import Any, Dict, List, Literal, Optional, Union

import jwt
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.actions.requests import ActionRequest, RequestActionException
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.resources.collections.filter import (
    build_filter,
    parse_condition_tree,
    parse_selection_ids,
)
from forestadmin.agent_toolkit.utils.context import FileResponse, HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.agent_toolkit.utils.forest_schema.action_values import ForestValueConverter
from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerActionField
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.exceptions import BusinessError
from forestadmin.datasource_toolkit.interfaces.actions import ActionsScope
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

LiteralMethod = Literal["execute", "hook"]


class ActionResource(BaseCollectionResource):
    @ip_white_list
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            request_collection = ActionRequest.from_request(request, self.datasource)
        except RequestActionException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])
        try:
            return await method(request_collection)
        except BusinessError as e:
            return HttpResponseBuilder.build_client_error_response([e])
        except Exception as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

    @check_method(RequestMethod.POST)
    @authenticate
    async def execute(self, request: ActionRequest) -> Union[FileResponse, Response]:
        if not request.body or not request.query:
            raise Exception

        self._middleware_custom_action_approval_request_data(request)  # where
        filter_ = await self._get_records_selection(request)
        await self.permission.can_smart_action(request, request.collection, filter_)

        raw_data: Dict[str, Any] = request.body.get("data", {}).get("attributes", {}).get("values", {})  # type: ignore

        # As forms are dynamic, we don't have any way to ensure that we're parsing the data correctly
        # => better send invalid data to the getForm() customer handler than to the execute() one.
        unsafe_data = ForestValueConverter.make_form_unsafe_data(raw_data)
        fields = await request.collection.get_form(request.user, request.action_name, unsafe_data, filter_)

        fields = SchemaActionGenerator.extract_fields_and_layout(fields)[0]
        # Now that we have the field list, we can parse the data again.
        data = ForestValueConverter.make_form_data(request.collection.datasource, raw_data, fields)
        result = await request.collection.execute(request.user, request.action_name, data, filter_)

        if result["type"] == ResultBuilder.ERROR:
            key = "error"
            if result["format"] == "html":
                key = "html"
            response = HttpResponseBuilder.build_json_response(400, {key: result["message"]})
        elif result["type"] == ResultBuilder.SUCCESS:
            key = "success"
            if result["format"] == "html":
                key = "html"
            response = HttpResponseBuilder.build_success_response({key: result["message"]})
        elif result["type"] == ResultBuilder.WEBHOOK:
            response = HttpResponseBuilder.build_success_response(
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
            response = FileResponse(
                result["stream"],
                result["name"],
                result["mimeType"],
                {"Access-Control-Expose-Headers": "Content-Disposition"},
            )

        elif result["type"] == ResultBuilder.REDIRECT:
            response = HttpResponseBuilder.build_success_response({"redirectTo": result["path"]})

        if "response_headers" in result:
            response.headers.update(result["response_headers"])

        return response

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
        unsafe_data: Optional[Dict[str, Any]] = None
        search_values = {}
        if forest_fields:
            unsafe_data = ForestValueConverter.make_form_data_from_fields(request.collection.datasource, forest_fields)
            for field in forest_fields:
                search_values[field["field"]] = field.get("searchValue")

        _filter = await self._get_records_selection(request)
        fields = await request.collection.get_form(
            request.user,
            request.action_name,
            unsafe_data,
            _filter,
            {
                "changed_field": request.body.get("data", {}).get("attributes", {}).get("changed_field"),
                "search_values": search_values,
                "search_field": request.body.get("data", {}).get("attributes", {}).get("search_field"),
            },
        )

        fields, layout = SchemaActionGenerator.extract_fields_and_layout(fields)
        ret = {
            "fields": [
                await SchemaActionGenerator.build_field_schema(request.collection.datasource, field) for field in fields
            ],
            "layout": [await SchemaActionGenerator.build_layout_schema(field) for field in layout],
        }
        return HttpResponseBuilder.build_success_response(ret)

    async def _get_records_selection(self, request: ActionRequest) -> Filter:
        trees: List[ConditionTree] = []
        attributes: Dict[str, Any] = request.body.get("data", {}).get("attributes", {})

        # Match user filter + search + scope? + segment.
        query_param_condition_tree = parse_condition_tree(request)
        if query_param_condition_tree:
            trees.append(query_param_condition_tree)
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        if scope_tree:
            trees.append(scope_tree)

        if trees:
            condition_tree = ConditionTreeFactory.intersect(trees)
        else:
            condition_tree = None
        filter_ = build_filter(request, condition_tree)

        # Restrict the filter to the selected records for single or bulk actions.
        if request.collection.schema["actions"][request.action_name].scope != ActionsScope.GLOBAL:
            selection_ids, exclude_ids = parse_selection_ids(request.collection.schema, request)
            selected_ids = ConditionTreeFactory.match_ids(request.collection.schema, selection_ids)
            if exclude_ids:
                selected_ids = selected_ids.inverse()
            if selected_ids != ConditionTreeBranch(Aggregator.OR, []):
                trees.append(selected_ids)
                filter_ = filter_.override(
                    {"condition_tree": ConditionTreeFactory.intersect([filter_.condition_tree, selected_ids])}
                )

        # Restrict the filter further for the "related data" page.
        if attributes.get("parent_association_name") is not None:
            parent = self.datasource.get_collection(attributes["parent_collection_name"])
            relation = parent.schema["fields"][attributes["parent_association_name"]]
            parent_id = unpack_id(parent.schema, attributes["parent_collection_id"])

            filter_ = await FilterFactory.make_foreign_filter(request.user, parent, parent_id, relation, filter_)
        return filter_

    def _middleware_custom_action_approval_request_data(self, request: ActionRequest):
        if request.body.get("data", {}).get("attributes", {}).get("signed_approval_request") is not None:
            attributes = self._decode_signed_approval_request(
                request.body["data"]["attributes"]["signed_approval_request"]
            )
            attributes["data"]["attributes"]["signed_approval_request"] = request.body["data"]["attributes"][
                "signed_approval_request"
            ]
            attributes["data"]["attributes"] = {
                k: v for k, v in attributes["data"]["attributes"].items() if v is not None
            }
            request.body = attributes
        return request

    def _decode_signed_approval_request(self, signed_approval_request):
        return jwt.decode(signed_approval_request, self.option["env_secret"], algorithms=["HS256"])
