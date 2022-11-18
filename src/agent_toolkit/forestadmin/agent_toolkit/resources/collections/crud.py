import asyncio
import sys

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from typing import Any, Awaitable, Dict, List, Tuple, cast

from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, authorize, check_method
from forestadmin.agent_toolkit.resources.collections.exceptions import CollectionResourceException
from forestadmin.agent_toolkit.resources.collections.filter import (
    FilterException,
    build_filter,
    build_paginated_filter,
    parse_condition_tree,
    parse_projection_with_pks,
    parse_selection_ids,
    parse_timezone,
)
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.serializers.json_api import JsonApiException, JsonApiSerializer
from forestadmin.agent_toolkit.utils.context import (
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_no_content_response,
    build_success_response,
    build_unknown_response,
)
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import (
    ManyToOne,
    OneToOne,
    Operator,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidatorException
from forestadmin.datasource_toolkit.validations.records import RecordValidator, RecordValidatorException
from typing_extensions import TypeGuard


def is_request_collection(request: Request) -> TypeGuard[RequestCollection]:
    return hasattr(request, "collection")


LiteralMethod = Literal["get", "list", "count", "add", "update", "delete", "delete_list", "update_list"]


class CrudResource(BaseCollectionResource):
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            return build_client_error_response([str(e)])
        return await method(request_collection)

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("read")
    async def get(self, request: RequestCollection) -> Response:
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        trees: List[ConditionTree] = [ConditionTreeFactory.match_ids(collection.schema, [ids])]
        scope_tree = await self.permission.get_scope(request)
        if scope_tree:
            trees.append(scope_tree)

        filter = PaginatedFilter({"condition_tree": ConditionTreeFactory.intersect(trees)})

        projections = ProjectionFactory.all(cast(Collection, collection))
        records = await collection.list(filter, projections)
        for name, schema in collection.schema["fields"].items():
            if is_many_to_many(schema):
                projections.append(f"{name}:id")  # type: ignore
                records[0][name] = None
        if not len(records):
            return build_unknown_response()
        else:
            schema = JsonApiSerializer.get(collection)
            try:
                dumped: Dict[str, Any] = schema(projections=projections).dump(records[0])  # type: ignore
            except JsonApiException as e:
                return build_client_error_response([str(e)])

        return build_success_response(dumped)

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("add")
    async def add(self, request: RequestCollection) -> Response:

        collection = request.collection
        schema = JsonApiSerializer.get(collection)
        try:
            data: RecordsDataAlias = schema().load(request.body)  # type: ignore
        except JsonApiException as e:
            return build_client_error_response([str(e)])

        record, one_to_one_relations = await self.extract_data(cast(Collection, collection), data)

        try:
            RecordValidator.validate(cast(Collection, collection), record)
        except RecordValidatorException as e:
            return build_client_error_response([str(e)])

        try:
            records = await collection.create([record])
        except DatasourceException as e:
            return build_client_error_response([str(e)])

        try:
            await self._link_one_to_one_relations(request, records[0], one_to_one_relations)
        except CollectionResourceException as e:
            return build_client_error_response([str(e)])

        return build_success_response(
            schema(projections=list(records[0].keys())).dump(records[0], many=False)  # type: ignore
        )

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("browse")
    async def list(self, request: RequestCollection) -> Response:
        scope_tree = await self.permission.get_scope(request)
        try:
            paginated_filter = build_paginated_filter(request, scope_tree)
        except FilterException as e:
            return build_client_error_response([str(e)])
        try:
            projections = parse_projection_with_pks(request)
        except DatasourceException as e:
            return build_client_error_response([str(e)])

        records = await request.collection.list(paginated_filter, projections)
        schema = JsonApiSerializer.get(request.collection)
        try:
            dumped: Dict[str, Any] = schema(projections=projections).dump(records, many=True)  # type: ignore
        except JsonApiException as e:
            return build_client_error_response([str(e)])
        return build_success_response(dumped)

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("browse")
    async def count(self, request: RequestCollection) -> Response:
        scope_tree = await self.permission.get_scope(request)
        filter = build_filter(request, scope_tree)
        aggregation = Aggregation({"operation": "Count"})
        result = await request.collection.aggregate(filter, aggregation)
        try:
            count = result[0]["value"]
        except IndexError:
            count = 0
        return build_success_response({"count": count})

    @check_method(RequestMethod.PUT)
    @authenticate
    @authorize("edit")
    async def update(self, request: RequestCollection) -> Response:
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        if request.body and "data" in request.body and "relationships" in request.body["data"]:
            del request.body["data"]["relationships"]

        schema = JsonApiSerializer.get(collection)
        try:
            data: RecordsDataAlias = schema().load(request.body)  # type: ignore
        except JsonApiException as e:
            return build_client_error_response([str(e)])
        try:
            RecordValidator.validate(cast(Collection, collection), data)
        except RecordValidatorException as e:
            return build_client_error_response([str(e)])

        trees: List[ConditionTree] = [ConditionTreeFactory.match_ids(collection.schema, [ids])]
        scope_tree = await self.permission.get_scope(request)
        if scope_tree:
            trees.append(scope_tree)

        filter = Filter({"condition_tree": ConditionTreeFactory.intersect(trees)})

        await collection.update(filter, data)
        projection = ProjectionFactory.all(cast(Collection, collection))
        records = await collection.list(PaginatedFilter.from_base_filter(filter), projection)

        schema = JsonApiSerializer.get(collection)
        try:
            dumped: Dict[str, Any] = schema(projections=projection).dump(records[0])  # type: ignore
        except JsonApiException as e:
            return build_client_error_response([str(e)])

        return build_success_response(dumped)

    @check_method(RequestMethod.DELETE)
    @authenticate
    @authorize("delete")
    async def delete(self, request: RequestCollection):
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        await self._delete(request, [ids])
        return build_no_content_response()

    @check_method(RequestMethod.DELETE)
    @authenticate
    @authorize("delete")
    async def delete_list(self, request: RequestCollection):
        ids, exclude_ids = parse_selection_ids(request)
        await self._delete(request, ids, exclude_ids)
        return build_no_content_response()

    async def _delete(self, request: RequestCollection, ids: List[CompositeIdAlias], exclude_ids: bool = False):
        selected_ids = ConditionTreeFactory.match_ids(request.collection.schema, ids)
        if exclude_ids:
            selected_ids = selected_ids.inverse()
        trees = [selected_ids]
        query_param_condition_tree = parse_condition_tree(request)
        if query_param_condition_tree:
            trees.append(query_param_condition_tree)
        scope_tree = await self.permission.get_scope(request)
        if scope_tree:
            trees.append(scope_tree)

        await request.collection.delete(build_filter(request, ConditionTreeFactory.intersect(trees)))

    async def _link_one_to_one_relation(
        self, request: RequestCollection, record: RecordsDataAlias, relation: OneToOne, linked: RecordsDataAlias
    ):
        foreign_collection = self.datasource.get_collection(relation["foreign_collection"])
        scope = await self.permission.get_scope(request, foreign_collection)
        await self.permission.can(request, f"edit:{request.collection.name}")
        origin_value = record[relation["origin_key_target"]]

        # Break the old relation
        old_fk_owner = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
        trees: List[ConditionTree] = [old_fk_owner]
        if scope:
            trees.append(scope)
        try:
            tz = parse_timezone(request)
        except FilterException as e:
            raise CollectionResourceException(str(e))

        await foreign_collection.update(
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": tz}),
            {
                f'{relation["origin_key"]}': None,
            },
        )

        # Create the new relation
        new_fk_owner = ConditionTreeFactory.match_records(foreign_collection.schema, [linked])
        trees: List[ConditionTree] = [new_fk_owner]
        if scope:
            trees.append(scope)

        await foreign_collection.update(
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": tz}),
            {
                f'{relation["origin_key"]}': origin_value,
            },
        )

    async def _link_one_to_one_relations(
        self, request: RequestCollection, record: RecordsDataAlias, relations: List[Tuple[OneToOne, RecordsDataAlias]]
    ):
        awaitables: List[Awaitable[None]] = []
        for relation, linked in relations:
            awaitables.append(self._link_one_to_one_relation(request, record, relation, linked))
        await asyncio.gather(*awaitables)

    async def extract_data(
        self, collection: Collection, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Tuple[OneToOne, RecordsDataAlias]]]:
        record: Dict[str, Any] = {}
        one_to_one_relations: List[Tuple[OneToOne, RecordsDataAlias]] = []
        for field_name, value in data.items():
            field = collection.get_field(field_name)
            if is_column(field):
                record[field_name] = value
            elif is_many_to_one(field) or is_one_to_one(field):
                foreign_collection = self.datasource.get_collection(field["foreign_collection"])
                pk_names = SchemaUtils.get_primary_keys(foreign_collection.schema)
                if is_one_to_one(field):
                    one_to_one_relations.append((field, dict([(pk, value[i]) for i, pk in enumerate(pk_names)])))
                else:
                    field = cast(ManyToOne, field)
                    record[field["foreign_key"]] = await CollectionUtils.get_value(
                        cast(Collection, foreign_collection), [value], field["foreign_key_target"]
                    )

        return record, one_to_one_relations
