import asyncio
from typing import Any, Awaitable, Dict, List, Literal, Optional, Tuple, Union, cast
from uuid import UUID

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import (
    authenticate,
    authorize,
    check_method,
    ip_white_list,
)
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
from forestadmin.agent_toolkit.resources.context_variable_injector_mixin import ContextVariableInjectorResourceMixin
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.services.serializers import add_search_metadata
from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiException
from forestadmin.agent_toolkit.services.serializers.json_api_deserializer import JsonApiDeserializer
from forestadmin.agent_toolkit.services.serializers.json_api_serializer import JsonApiSerializer
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response, User
from forestadmin.agent_toolkit.utils.csv import Csv, CsvException
from forestadmin.agent_toolkit.utils.id import IdException, unpack_id
from forestadmin.agent_toolkit.utils.sql_query_checker import SqlQueryChecker
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, NativeQueryException
from forestadmin.datasource_toolkit.interfaces.fields import (
    ManyToOne,
    OneToOne,
    Operator,
    PolymorphicOneToOne,
    PrimitiveType,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidatorException
from forestadmin.datasource_toolkit.validations.records import RecordValidator, RecordValidatorException

LiteralMethod = Literal["list", "count", "add", "get", "delete_list", "csv"]


class CrudResource(BaseCollectionResource, ContextVariableInjectorResourceMixin):
    def __init__(
        self,
        datasource_composite: CompositeDatasource,
        datasource: Union[Datasource, DatasourceCustomizer],
        permission: PermissionService,
        ip_white_list_service: IpWhiteListService,
        options: Options,
    ):
        self._datasource_composite = datasource_composite
        super().__init__(datasource, permission, ip_white_list_service, options)

    @ip_white_list
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        try:
            return await method(request_collection)
        except ForbiddenError as exc:
            return HttpResponseBuilder.build_client_error_response([exc])
        except Exception as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("read")
    async def get(self, request: RequestCollection) -> Response:
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        trees: List[ConditionTree] = [ConditionTreeFactory.match_ids(collection.schema, [ids])]
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        if scope_tree:
            trees.append(scope_tree)

        filter = PaginatedFilter({"condition_tree": ConditionTreeFactory.intersect(trees)})

        projections = parse_projection_with_pks(request)
        records = await collection.list(request.user, filter, projections)

        if not len(records):
            return HttpResponseBuilder.build_unknown_response()

        try:
            dumped: Dict[str, Any] = self._serialize_records_with_relationships(
                records, request.collection, projections, many=False
            )
        except JsonApiException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        return HttpResponseBuilder.build_success_response(dumped)

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("add")
    async def add(self, request: RequestCollection) -> Response:
        collection = request.collection
        try:
            data = JsonApiDeserializer(self.datasource).deserialize(request.body, collection)
        except JsonApiException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        record, one_to_one_relations = await self.extract_data(request.user, cast(Collection, collection), data)

        try:
            RecordValidator.validate(cast(Collection, collection), record)
        except RecordValidatorException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        try:
            records = await collection.create(request.user, [record])
        except DatasourceException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        try:
            await self._link_one_to_one_relations(request, records[0], one_to_one_relations)
        except CollectionResourceException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        return HttpResponseBuilder.build_success_response(
            self._serialize_records_with_relationships(
                records, request.collection, Projection(*list(records[0].keys())), many=False
            )
        )

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("browse")
    async def list(self, request: RequestCollection) -> Response:
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        try:
            paginated_filter = build_paginated_filter(request, scope_tree)
            condition_tree = await self._handle_live_query_segment(request, paginated_filter.condition_tree)
            paginated_filter = paginated_filter.override({"condition_tree": condition_tree})

        except FilterException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])
        try:
            projections = parse_projection_with_pks(request)
        except DatasourceException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        records = await request.collection.list(request.user, paginated_filter, projections)

        try:
            dumped: Dict[str, Any] = self._serialize_records_with_relationships(
                records, request.collection, projections, many=True
            )
        except JsonApiException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        if paginated_filter.search:
            dumped = add_search_metadata(dumped, paginated_filter.search)

        return HttpResponseBuilder.build_success_response(dumped)

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("browse")
    @authorize("export")
    async def csv(self, request: RequestCollection) -> Response:
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        try:
            paginated_filter = build_paginated_filter(request, scope_tree)
            condition_tree = await self._handle_live_query_segment(request, paginated_filter.condition_tree)
            paginated_filter = paginated_filter.override({"condition_tree": condition_tree})
            paginated_filter.page = None
        except FilterException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])
        try:
            projections = parse_projection_with_pks(request)
        except DatasourceException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        records = await request.collection.list(request.user, paginated_filter, projections)

        try:
            csv_str = Csv.make_csv(records, projections)
        except CsvException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])
        return HttpResponseBuilder.build_csv_response(
            csv_str, f"{request.query.get('filename', request.collection.name)}.csv"
        )

    @check_method(RequestMethod.GET)
    @authenticate
    @authorize("browse")
    async def count(self, request: RequestCollection) -> Response:
        if request.collection.schema["countable"] is False:
            return HttpResponseBuilder.build_success_response({"meta": {"count": "deactivated"}})

        scope_tree = await self.permission.get_scope(request.user, request.collection)
        filter_ = build_filter(request, scope_tree)
        filter_ = filter_.override(
            {"condition_tree": await self._handle_live_query_segment(request, filter_.condition_tree)}
        )
        aggregation = Aggregation({"operation": "Count"})
        result = await request.collection.aggregate(request.user, filter_, aggregation)
        try:
            count = result[0]["value"]
        except IndexError:
            count = 0
        return HttpResponseBuilder.build_success_response({"count": count})

    @check_method(RequestMethod.PUT)
    @authenticate
    @authorize("edit")
    async def update(self, request: RequestCollection) -> Response:
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException, IdException) as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        if request.body and "data" in request.body and "relationships" in request.body["data"]:
            del request.body["data"]["relationships"]

        try:
            # if the id change it will be in 'data.attributes', otherwise, we get the id by from the request url.
            request.body["data"].pop("id", None)  # type: ignore
            data = JsonApiDeserializer(self.datasource).deserialize(request.body, collection)
        except JsonApiException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        trees: List[ConditionTree] = [ConditionTreeFactory.match_ids(collection.schema, [ids])]
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        if scope_tree:
            trees.append(scope_tree)

        filter = Filter({"condition_tree": ConditionTreeFactory.intersect(trees)})

        await collection.update(request.user, filter, data)
        projection = ProjectionFactory.all(cast(Collection, collection))
        records = await collection.list(request.user, PaginatedFilter.from_base_filter(filter), projection)

        try:
            dumped: Dict[str, Any] = self._serialize_records_with_relationships(
                records, request.collection, projection, many=False
            )
        except JsonApiException as e:
            return HttpResponseBuilder.build_client_error_response([e])

        return HttpResponseBuilder.build_success_response(dumped)

    @check_method(RequestMethod.DELETE)
    @authenticate
    @authorize("delete")
    async def delete(self, request: RequestCollection):
        collection = request.collection
        try:
            ids = unpack_id(collection.schema, request.pks)
        except (FieldValidatorException, CollectionResourceException) as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        await self._delete(request, [ids])
        return HttpResponseBuilder.build_no_content_response()

    @check_method(RequestMethod.DELETE)
    @authenticate
    @authorize("delete")
    async def delete_list(self, request: RequestCollection):
        ids, exclude_ids = parse_selection_ids(request.collection.schema, request)
        await self._delete(request, ids, exclude_ids)
        return HttpResponseBuilder.build_no_content_response()

    async def _delete(self, request: RequestCollection, ids: List[CompositeIdAlias], exclude_ids: bool = False):
        selected_ids = ConditionTreeFactory.match_ids(request.collection.schema, ids)
        if exclude_ids:
            selected_ids = selected_ids.inverse()
        trees = [selected_ids]
        query_param_condition_tree = parse_condition_tree(request)
        if query_param_condition_tree:
            trees.append(query_param_condition_tree)
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        if scope_tree:
            trees.append(scope_tree)

        await request.collection.delete(request.user, build_filter(request, ConditionTreeFactory.intersect(trees)))

    async def _link_one_to_one_relation(
        self,
        request: RequestCollection,
        record: RecordsDataAlias,
        relation: Union[OneToOne, PolymorphicOneToOne],
        linked: RecordsDataAlias,
    ):
        foreign_collection = self.datasource.get_collection(relation["foreign_collection"])
        scope = await self.permission.get_scope(request.user, foreign_collection)
        await self.permission.can(request.user, request.collection, "edit")
        origin_value = record[relation["origin_key_target"]]

        # not needed
        # Break the old relation
        old_fk_owner = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
        trees: List[ConditionTree] = [old_fk_owner]
        if scope:
            trees.append(scope)

        try:
            tz = parse_timezone(request)
        except FilterException as e:
            raise CollectionResourceException(str(e)[3:])

        patch = {f'{relation["origin_key"]}': None}
        if is_polymorphic_one_to_one(relation):
            patch[relation["origin_type_field"]] = None
            trees.append(ConditionTreeLeaf(relation["origin_type_field"], "equal", relation["origin_type_value"]))

        await foreign_collection.update(
            request.user,
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": tz}),
            patch,
        )

        # Create the new relation
        new_fk_owner = ConditionTreeFactory.match_records(foreign_collection.schema, [linked])
        trees: List[ConditionTree] = [new_fk_owner]
        if scope:
            trees.append(scope)
        patch = {f'{relation["origin_key"]}': origin_value}
        if is_polymorphic_one_to_one(relation):
            patch[relation["origin_type_field"]] = relation["origin_type_value"]

        await foreign_collection.update(
            request.user,
            Filter({"condition_tree": ConditionTreeFactory.intersect(trees), "timezone": tz}),
            patch,
        )

    async def _link_one_to_one_relations(
        self, request: RequestCollection, record: RecordsDataAlias, relations: List[Tuple[OneToOne, RecordsDataAlias]]
    ):
        awaitables: List[Awaitable[None]] = []
        for relation, linked in relations:
            awaitables.append(self._link_one_to_one_relation(request, record, relation, linked))
        await asyncio.gather(*awaitables)

    async def extract_data(
        self, caller: User, collection: Collection, data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[Tuple[OneToOne, RecordsDataAlias]]]:
        record: Dict[str, Any] = {}
        one_to_one_relations: List[Tuple[OneToOne, RecordsDataAlias]] = []
        for field_name, value in data.items():
            field = collection.get_field(field_name)
            if is_column(field):
                if field["column_type"] == PrimitiveType.UUID:
                    record[field_name] = UUID(value) if isinstance(value, str) else value
                else:
                    record[field_name] = value
            elif (
                is_many_to_one(field)
                or is_one_to_one(field)
                or is_polymorphic_one_to_one(field)
                or is_polymorphic_many_to_one(field)
            ):
                foreign_collection = self.datasource.get_collection(field["foreign_collection"])
                pk_names = SchemaUtils.get_primary_keys(foreign_collection.schema)
                if is_one_to_one(field) or is_polymorphic_one_to_one(field):
                    one_to_one_relations.append((field, dict([(pk, value) for pk in pk_names])))
                    # one_to_one_relations.append((field, dict([(pk, value[i]) for i, pk in enumerate(pk_names)])))
                else:
                    field = cast(ManyToOne, field)
                    value = await CollectionUtils.get_value(
                        caller, cast(Collection, foreign_collection), [value], field["foreign_key_target"]
                    )
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    record[field["foreign_key"]] = value

        return record, one_to_one_relations

    def _serialize_records_with_relationships(
        self,
        records: List[RecordsDataAlias],
        collection: Union[Collection, CollectionCustomizer],
        projection: Projection,
        many: bool,
    ) -> Dict[str, Any]:
        relations_to_set = []
        projection = Projection(*projection)
        for name, schema in collection.schema["fields"].items():
            if is_many_to_many(schema) or is_one_to_many(schema) or is_polymorphic_one_to_many(schema):
                pks = SchemaUtils.get_primary_keys(
                    collection.datasource.get_collection(schema["foreign_collection"]).schema
                )
                for pk in pks:
                    projection.append(f"{name}:{pk}")
                relations_to_set.append(name)

        for record in records:
            for name in relations_to_set:
                record[name] = None

        ret = JsonApiSerializer(self.datasource, projection).serialize(
            records if many is True else records[0], collection
        )
        return ret

    async def _handle_live_query_segment(
        self, request: RequestCollection, condition_tree: Optional[ConditionTree]
    ) -> Optional[ConditionTree]:
        if request.query.get("segmentQuery") is not None:
            if request.query.get("connectionName") in ["", None]:
                raise NativeQueryException("Missing native query connection attribute")

            await self.permission.can_live_query_segment(request)
            SqlQueryChecker.check_query(request.query["segmentQuery"])
            variables = await self.inject_and_get_context_variables_in_live_query_segment(request)
            native_query_result = await self._datasource_composite.execute_native_query(
                request.query["connectionName"], request.query["segmentQuery"], variables
            )

            pk_field = SchemaUtils.get_primary_keys(request.collection.schema)[0]
            if len(native_query_result) > 0 and pk_field not in native_query_result[0]:
                raise NativeQueryException(f"Live query must return the primary key field ('{pk_field}').")

            trees = []
            if condition_tree:
                trees.append(condition_tree)
            trees.append(
                ConditionTreeFactory.match_ids(
                    request.collection.schema,
                    [RecordUtils.get_primary_key(request.collection.schema, r) for r in native_query_result],
                )
            )
            return ConditionTreeFactory.intersect(trees)
        return condition_tree
