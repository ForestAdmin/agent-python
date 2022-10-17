import sys

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal
if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from typing import Any, Dict, List, Union, cast

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
from forestadmin.agent_toolkit.resources.collections.requests import (
    RequestCollectionException,
    RequestRelationCollection,
)
from forestadmin.agent_toolkit.services.serializers import DumpedResult, add_search_metadata
from forestadmin.agent_toolkit.services.serializers.json_api import JsonApiException, JsonApiSerializer
from forestadmin.agent_toolkit.utils.context import (
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_no_content_response,
    build_success_response,
)
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import (
    Operator,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidatorException

LiteralMethod = Literal["list", "add", "delete", "update"]


class CrudRelatedResource(BaseCollectionResource):
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            request_collection = RequestRelationCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            return build_client_error_response([str(e)])
        return await method(request_collection)

    @authenticate
    @authorize("browse")
    @check_method(RequestMethod.GET)
    async def list(self, request: RequestRelationCollection) -> Response:
        if not (is_one_to_many(request.relation) or is_many_to_many(request.relation)):
            return build_client_error_response(["Unhandled relation type"])
        try:
            ids = unpack_id(request.collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])
        scope_tree = await self.permission.get_scope(request, request.foreign_collection)
        paginated_filter = build_paginated_filter(request, scope_tree)
        projection = parse_projection_with_pks(request)
        records = await CollectionUtils.list_relation(
            cast(Collection, request.collection),
            ids,
            cast(Collection, request.foreign_collection),
            request.relation,
            paginated_filter,
            projection,
        )
        schema = JsonApiSerializer.get(request.foreign_collection)
        try:
            dumped: DumpedResult = schema(projections=projection).dump(records, many=True)  # type: ignore
        except JsonApiException as e:
            return build_client_error_response([str(e)])

        if paginated_filter.search:
            dumped = add_search_metadata(dumped, paginated_filter.search)

        return build_success_response(cast(Dict[str, Any], dumped))

    @authenticate
    @authorize("edit")
    @check_method(RequestMethod.POST)
    async def add(self, request: RequestRelationCollection) -> Response:
        try:
            parent_ids = unpack_id(request.collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        if (
            not request.body
            or "data" not in request.body
            or len(request.body["data"]) == 0
            or not request.body["data"][0].get("id")
        ):
            return build_client_error_response(["missing target's id "])
        try:
            targeted_relation_ids = unpack_id(request.foreign_collection.schema, request.body["data"][0]["id"])
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        if not (is_one_to_many(request.relation) or is_many_to_many(request.relation)):
            return build_client_error_response(["Unhandled relation type"])

        pks = SchemaUtils.get_primary_keys(request.foreign_collection.schema)[0]
        value = await CollectionUtils.get_value(
            cast(Collection, request.foreign_collection), targeted_relation_ids, pks
        )
        if is_one_to_many(request.relation):
            return await self._associate_one_to_many(request, parent_ids, value)
        else:
            return await self._associate_many_to_many(request, parent_ids, value)

    @authenticate
    @authorize("edit")
    @check_method(RequestMethod.PUT)
    async def update_list(self, request: RequestRelationCollection) -> Response:
        try:
            timezone = parse_timezone(request)
        except FilterException as e:
            return build_client_error_response([str(e)])
        try:
            parent_id = unpack_id(request.collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])
        if not request.body or not request.body.get("data") or "id" not in request.body["data"]:
            return build_client_error_response(["Relation id is missing"])
        try:
            linked_id = unpack_id(request.foreign_collection.schema, request.body["data"]["id"])
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        if is_many_to_one(request.relation) or is_one_to_one(request.relation):

            if is_many_to_one(request.relation):
                meth = self._update_many_to_one
            else:
                meth = self._update_one_to_one

            try:
                await meth(request, parent_id, linked_id, timezone)
            except (CollectionResourceException, DatasourceException) as e:
                return build_client_error_response([str(e)])
            return build_no_content_response()
        return build_client_error_response(["Unhandled relation type"])

    @authenticate
    @authorize("browse")
    @check_method(RequestMethod.GET)
    async def count(self, request: RequestRelationCollection) -> Response:
        try:
            parent_id = unpack_id(request.collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])
        scope_tree = await self.permission.get_scope(request, request.foreign_collection)
        filter = build_filter(request, scope_tree)
        aggregation = Aggregation({"operation": "Count"})

        result = await CollectionUtils.aggregate_relation(
            cast(Collection, request.collection), parent_id, request.relation_name, filter, aggregation
        )
        try:
            count = result[0]["value"]
        except IndexError:
            count = 0
        return build_success_response({"count": count})

    @authenticate
    @authorize("delete")
    @check_method(RequestMethod.DELETE)
    async def delete_list(self, request: RequestRelationCollection) -> Response:
        try:
            parent_ids = unpack_id(request.collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            return build_client_error_response([str(e)])

        delete_mode = False
        if request.query:
            delete_mode = bool(request.query.get("delete", False))

        filter = await self.get_base_fk_filter(request)

        if is_one_to_many(request.relation) or is_many_to_many(request.relation):
            if is_one_to_many(request.relation):
                meth = self._delete_one_to_many
            else:
                meth = self._delete_many_to_many
            try:
                await meth(request, parent_ids, delete_mode, filter)
            except (DatasourceException, CollectionResourceException) as e:
                return build_client_error_response([str(e)])
            return build_no_content_response()
        return build_client_error_response(["Unhandled relation type"])

    async def _associate_one_to_many(
        self, request: RequestRelationCollection, parent_ids: CompositeIdAlias, id_value: Union[str, int]
    ) -> Response:
        if not is_one_to_many(request.relation):
            raise
        scope_tree = await self.permission.get_scope(request, request.foreign_collection)
        filter = build_filter(request, scope_tree)
        trees: List[ConditionTree] = [
            ConditionTreeLeaf("id", Operator.EQUAL, id_value),
        ]
        if filter.condition_tree:
            trees.append(filter.condition_tree)
        filter.condition_tree = ConditionTreeFactory.intersect(trees)
        value = await CollectionUtils.get_value(
            cast(Collection, request.collection), parent_ids, request.relation["origin_key_target"]
        )
        try:
            await request.foreign_collection.update(filter, {f"{request.relation['origin_key']}": value})
        except DatasourceException as e:
            return build_client_error_response([str(e)])
        else:
            return build_no_content_response()

    async def _associate_many_to_many(
        self, request: RequestRelationCollection, parent_ids: CompositeIdAlias, foreign_id_value: Union[str, int]
    ):
        if not is_many_to_many(request.relation):
            raise
        id = SchemaUtils.get_primary_keys(request.collection.schema)
        origin_id_value = await CollectionUtils.get_value(cast(Collection, request.collection), parent_ids, id[0])

        record = {
            f"{request.relation['origin_key']}": origin_id_value,
            f"{request.relation['foreign_key']}": foreign_id_value,
        }
        through_collection = request.collection.datasource.get_collection(request.relation["through_collection"])
        try:
            await through_collection.create([record])
        except DatasourceException as e:
            return build_client_error_response([str(e)])
        else:
            return build_no_content_response()

    async def get_base_fk_filter(self, request: RequestRelationCollection):
        ids, exclude_ids = parse_selection_ids(request)

        if len(ids) == 0 and not exclude_ids:
            raise

        selected_ids = ConditionTreeFactory.match_ids(request.foreign_collection.schema, ids)
        if exclude_ids:
            selected_ids = selected_ids.inverse()

        scope_tree = await self.permission.get_scope(request, request.foreign_collection)
        filter = build_filter(request, scope_tree)
        trees = [selected_ids]
        if scope_tree:
            trees.append(scope_tree)
        parsed_tree = parse_condition_tree(request)
        if parsed_tree:
            trees.append(parsed_tree)
        filter.condition_tree = ConditionTreeFactory.intersect(trees)
        return filter

    async def _delete_one_to_many(
        self,
        request: RequestRelationCollection,
        parent_id: CompositeIdAlias,
        is_delete: bool,
        base_target_filter: Filter,
    ):
        if not is_one_to_many(request.relation):
            raise CollectionResourceException("Unhandled relation type")
        foreign_paginated_filter = await FilterFactory.make_foreign_filter(
            cast(Collection, request.collection), parent_id, request.relation, base_target_filter
        )
        foreign_filter = foreign_paginated_filter.to_base_filter()
        if is_delete:
            await request.foreign_collection.delete(foreign_filter)
        else:
            await request.foreign_collection.update(foreign_filter, {f"{request.relation['origin_key']}": None})

    async def _delete_many_to_many(
        self,
        request: RequestRelationCollection,
        parent_id: CompositeIdAlias,
        is_delete: bool,
        base_target_filter: Filter,
    ):
        if not is_many_to_many(request.relation):
            raise CollectionResourceException("Unhandled relation type")
        through_filter = await FilterFactory.make_through_filter(
            cast(Collection, request.collection),
            parent_id,
            request.relation,
            base_target_filter,
        )
        through_collection = request.collection.datasource.get_collection(request.relation["through_collection"])
        if is_delete:
            foreign_filter = await FilterFactory.make_foreign_filter(
                cast(Collection, request.collection), parent_id, request.relation, base_target_filter
            )
            await through_collection.delete(through_filter.to_base_filter())
            try:
                await request.foreign_collection.delete(foreign_filter.to_base_filter())
            except DatasourceException:
                # Let the datasource crash when:
                # - the records in the foreignCollection are linked to other records in the origin collection
                # - the underlying database/api is not cascading deletes
                pass
        else:
            await through_collection.delete(through_filter.to_base_filter())

    async def _update_one_to_one(
        self,
        request: RequestRelationCollection,
        parent_id: CompositeIdAlias,
        linked_id: CompositeIdAlias,
        timezone: zoneinfo.ZoneInfo,
    ):
        if not is_one_to_one(request.relation):
            raise CollectionResourceException("Unhandled relation type")

        scope = await self.permission.get_scope(request)
        origin_value = await CollectionUtils.get_value(
            cast(Collection, request.collection), parent_id, request.relation["origin_key_target"]
        )

        trees: List[ConditionTree] = [ConditionTreeLeaf(request.relation["origin_key"], Operator.EQUAL, origin_value)]
        if scope:
            trees.append(scope)

        await request.foreign_collection.update(
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": timezone}),
            {f"{request.relation['origin_key']}": origin_value},
        )

        trees = [ConditionTreeFactory.match_ids(request.foreign_collection.schema, [linked_id])]
        if scope:
            trees.append(scope)
        await request.foreign_collection.update(
            Filter(
                {
                    "condition_tree": ConditionTreeFactory.intersect(trees),
                    "timezone": timezone,
                }
            ),
            {f"{request.relation['origin_key']}": origin_value},
        )

    async def _update_many_to_one(
        self,
        request: RequestRelationCollection,
        parent_id: CompositeIdAlias,
        linked_id: CompositeIdAlias,
        timezone: zoneinfo.ZoneInfo,
    ):
        if not is_many_to_one(request.relation):
            raise CollectionResourceException("Unhandled relation type")

        scope = await self.permission.get_scope(request)
        foreign_value = await CollectionUtils.get_value(
            cast(Collection, request.collection), linked_id, request.relation["foreign_key_target"]
        )

        trees = [ConditionTreeFactory.match_ids(request.collection.schema, [parent_id])]
        if scope:
            trees.append(scope)

        await request.collection.update(
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": timezone}),
            {f"{request.relation['foreign_key']}": foreign_value},
        )
