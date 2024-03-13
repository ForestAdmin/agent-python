from typing import Dict, List, Optional, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.relation.types import RelationDefinition
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldAlias, FieldType, Operator, RelationAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class RelationCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._relations: Dict[str, RelationAlias] = {}

    def add_relation(self, name: str, partial_join: RelationDefinition):
        relation = self._relation_with_optional_fields(partial_join)
        self._check_foreign_keys(relation)
        self._check_origin_keys(relation)

        self._relations[name] = relation
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        schema = {**sub_schema, "fields": {**sub_schema["fields"]}}
        for name, relation in self._relations.items():
            schema["fields"][name] = relation
        return schema

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        new_filter = await self._refine_filter(caller, _filter)
        new_projection = projection.replace(self._rewrite_field).with_pks(self)
        records = await self.child_collection.list(caller, new_filter, new_projection)
        if new_projection == projection:
            return records

        await self._reproject_in_place(caller, records, projection)

        return projection.apply(records)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        new_filter = await self._refine_filter(caller, _filter)

        # No emulated relations are used in the aggregation
        if len([r for r in aggregation.projection.relations.keys() if r in self._relations.keys()]) == 0:
            return await self.child_collection.aggregate(caller, new_filter, aggregation, limit)

        # Fallback to full emulation
        return aggregation.apply(
            await self.list(caller, PaginatedFilter.from_base_filter(_filter), aggregation.projection),
            caller.timezone,
            limit,
        )

    async def _refine_filter(
        self, caller: User, _filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        if _filter is None:
            return None

        async def call_rewrite_leaf(leaf):
            return await self._rewrite_leaf(caller, leaf)

        if _filter.condition_tree is not None:
            new_condition_tree = await _filter.condition_tree.replace_async(call_rewrite_leaf)
        else:
            new_condition_tree = None

        # Replace sort in emulated relations to
        # - sorting by the fk of the relation for many to one
        # - removing the sort altogether for one to one
        #
        # This is far from ideal, but the best that can be done without taking a major
        # performance hit.
        # Customers which want proper sorting should enable emulation in the associated
        # middleware
        if isinstance(_filter, PaginatedFilter):
            if _filter.sort is not None:
                new_sort = _filter.sort.replace_clauses(
                    lambda clause: [{**clause, "field": field} for field in self._rewrite_field(clause["field"])]
                )
            else:
                new_sort = None

            return _filter.override({"condition_tree": new_condition_tree, "sort": new_sort})
        else:
            return _filter.override({"condition_tree": new_condition_tree})

    def _relation_with_optional_fields(self, partial_joint: RelationDefinition) -> RelationAlias:
        relation: RelationDefinition = {**partial_joint}
        target: Collection = self.datasource.get_collection(relation["foreign_collection"])

        if relation["type"] == FieldType.MANY_TO_ONE:
            if relation.get("foreign_key_target") is None:
                relation["foreign_key_target"] = SchemaUtils.get_primary_keys(target.schema)[0]
        elif relation["type"] in [FieldType.ONE_TO_ONE, FieldType.ONE_TO_MANY]:
            if relation.get("origin_key_target") is None:
                relation["origin_key_target"] = SchemaUtils.get_primary_keys(self.schema)[0]
        elif relation["type"] == FieldType.MANY_TO_MANY:
            if relation.get("origin_key_target") is None:
                relation["origin_key_target"] = SchemaUtils.get_primary_keys(self.schema)[0]
            if relation.get("foreign_key_target") is None:
                relation["foreign_key_target"] = SchemaUtils.get_primary_keys(target.schema)[0]

        return relation

    def _check_foreign_keys(self, relation: RelationAlias):
        if relation["type"] in [FieldType.MANY_TO_ONE, FieldType.MANY_TO_MANY]:
            if relation["type"] == FieldType.MANY_TO_MANY:
                owner = self.datasource.get_collection(relation["through_collection"])
            else:
                owner = self

            RelationCollectionDecorator._check_keys(
                owner,
                self.datasource.get_collection(relation["foreign_collection"]),
                relation["foreign_key"],
                relation["foreign_key_target"],
            )

    def _check_origin_keys(self, relation: RelationAlias):
        if relation["type"] in [FieldType.ONE_TO_MANY, FieldType.ONE_TO_ONE, FieldType.MANY_TO_MANY]:
            if relation["type"] == FieldType.MANY_TO_MANY:
                owner = self.datasource.get_collection(relation["through_collection"])
            else:
                owner = self.datasource.get_collection(relation["foreign_collection"])
            RelationCollectionDecorator._check_keys(owner, self, relation["origin_key"], relation["origin_key_target"])

    @staticmethod
    def _check_keys(owner: Collection, target_owner: Collection, key_name: str, target_name: str):
        RelationCollectionDecorator._check_column(owner, key_name)
        RelationCollectionDecorator._check_column(target_owner, target_name)

        key: Column = owner.schema["fields"][key_name]
        target: Column = target_owner.schema["fields"][target_name]

        if key["column_type"] != target["column_type"]:
            raise ForestException(
                f"Types from '{owner.name}.{key_name}' and '{target_owner.name}.{target_name}' do not match."
            )

    @staticmethod
    def _check_column(owner: Collection, name: str):
        FieldValidator.validate(owner, name)
        column = owner.schema["fields"][name]

        if column["type"] != FieldType.COLUMN:
            raise ForestException(f"Column not found: '{owner.name}.{name}'")

        if Operator.IN not in column.get("filter_operators", []):
            raise ForestException(f"Column does not support the In operator: '{owner.name}.{name}'")

    def _rewrite_field(self, field: str) -> List[str]:
        prefix = field.split(":")[0]
        schema: FieldAlias = self.schema["fields"][prefix]
        if schema["type"] == FieldType.COLUMN:
            return [field]

        relation = self.datasource.get_collection(schema["foreign_collection"])
        result = []
        if self._relations.get(prefix) is None:
            result = [f"{prefix}:{sub_field}" for sub_field in relation._rewrite_field(field[len(prefix) + 1 :])]
        elif schema["type"] == FieldType.MANY_TO_ONE:
            result = [schema["foreign_key"]]
        elif schema["type"] in [FieldType.ONE_TO_ONE, FieldType.ONE_TO_MANY, FieldType.MANY_TO_MANY]:
            result = [schema["origin_key_target"]]
        return result

    async def _rewrite_leaf(self, caller: User, leaf: ConditionTreeLeaf) -> ConditionTree:
        prefix = leaf.field.split(":")[0]
        schema: FieldAlias = self.schema["fields"][prefix]
        if schema["type"] == FieldType.COLUMN:
            return leaf

        relation = self.datasource.get_collection(schema["foreign_collection"])

        if self._relations.get(prefix) is None:
            return (await relation._rewrite_leaf(caller, leaf.unnest())).nest(prefix)

        elif schema["type"] in [FieldType.MANY_TO_ONE, FieldType.ONE_TO_ONE]:
            if schema["type"] == FieldType.MANY_TO_ONE:
                projection_field = schema["foreign_key_target"]
                condition_tree_field = schema["foreign_key"]
            else:
                projection_field = schema["origin_key"]
                condition_tree_field = schema["origin_key_target"]

            records = await relation.list(
                caller, PaginatedFilter({"condition_tree": leaf.unnest()}), Projection(projection_field)
            )

            values = set()
            for record in records:
                v = RecordUtils.get_field_value(record, projection_field)
                if v is not None:
                    values.add(v)

            return ConditionTreeLeaf(condition_tree_field, Operator.IN, [*values])

        else:
            return leaf

    async def _reproject_in_place(self, caller: User, records: List[RecordsDataAlias], projection: Projection):
        for prefix, sub_projection in projection.relations.items():
            await self._reproject_relation_in_place(caller, records, prefix, sub_projection)

    async def _reproject_relation_in_place(
        self, caller: User, records: List[RecordsDataAlias], name: str, projection: Projection
    ):
        schema = self.schema["fields"][name]
        association = self.datasource.get_collection(schema["foreign_collection"])
        if self._relations.get(name) is None:
            await association._reproject_in_place(caller, [r[name] for r in records if r.get(name)], projection)

        elif schema["type"] == FieldType.MANY_TO_ONE:
            ids = [record[schema["foreign_key"]] for record in records if record[schema.get("foreign_key")]]
            sub_filter = PaginatedFilter(
                {"condition_tree": ConditionTreeLeaf(schema["foreign_key_target"], Operator.IN, [*set(ids)])}
            )

            sub_records = await association.list(caller, sub_filter, projection.union([schema["foreign_key_target"]]))
            for record in records:
                founds = [
                    *filter(lambda sr: sr[schema["foreign_key_target"]] == record[schema["foreign_key"]], sub_records)
                ]
                record[name] = founds[0] if len(founds) > 0 else None

        elif schema["type"] in [FieldType.ONE_TO_ONE, FieldType.ONE_TO_MANY]:
            ids = [record[schema["origin_key_target"]] for record in records if record[schema.get("origin_key_target")]]
            sub_filter = PaginatedFilter(
                {"condition_tree": ConditionTreeLeaf(schema["origin_key"], Operator.IN, [*set(ids)])}
            )

            sub_records = await association.list(caller, sub_filter, projection.union([schema["origin_key"]]))

            for record in records:
                founds = [
                    *filter(lambda sr: sr[schema["origin_key"]] == record[schema["origin_key_target"]], sub_records)
                ]
                record[name] = founds[0] if len(founds) > 0 else None
