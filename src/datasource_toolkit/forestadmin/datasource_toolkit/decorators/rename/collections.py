from typing import Any, Dict, List, Optional

from forestadmin.datasource_toolkit.decorators.collections import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldAlias,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    CollectionSchema,
    Datasource,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    AggregateResult,
    Aggregation,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import (
    PaginatedFilter,
    PaginatedFilterComponent,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class RenameCollectionException(DatasourceToolkitException):
    pass


class RenameCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource["RenameCollectionDecorator"]):
        super().__init__(collection, datasource)
        self.to_child_collection: Dict[str, str] = {}
        self.from_child_collection: Dict[str, str] = {}

    def rename_field(self, current_name: str, new_name: str):
        if current_name not in self.schema["fields"]:
            raise RenameCollectionException(f"So such field {current_name}")

        initial_name = current_name
        if current_name in self.to_child_collection:
            child_name = self.to_child_collection[current_name]
            del self.to_child_collection[current_name]
            del self.from_child_collection[child_name]
            initial_name = child_name
            self.mark_schema_as_dirty()

        if initial_name != new_name:
            self.from_child_collection[initial_name] = new_name
            self.to_child_collection[new_name] = initial_name
            self.mark_schema_as_dirty()

    def _refine_schema(self, child_schema: CollectionSchema) -> CollectionSchema:
        fields: Dict[str, FieldAlias] = {}
        for old_name, old_schema in child_schema["fields"].items():
            schema = old_schema.copy()
            if is_many_to_many(schema):
                schema["foreign_key"] = self.from_child_collection.get(schema["foreign_key"], schema["foreign_key"])
            elif is_one_to_many(schema) or is_one_to_one(schema):
                relation = self.datasource.get_collection(schema["foreign_collection"])
                schema["origin_key"] = relation.from_child_collection.get(schema["origin_key"], schema["origin_key"])
            elif is_many_to_many(schema):
                through = self.datasource.get_collection(schema["through_collection"])
                schema["foreign_key"] = through.from_child_collection.get(schema["foreign_key"], schema["foreign_key"])
                schema["origin_key"] = through.from_child_collection.get(schema["origin_key"], schema["origin_key"])
            fields[self.from_child_collection.get(old_name, old_name)] = schema

        refined_schema = child_schema.copy()
        refined_schema["fields"] = fields
        return refined_schema

    def _refine_leaf_tree(self, tree: ConditionTree) -> ConditionTree:
        if isinstance(tree, ConditionTreeLeaf):
            tree.field = self.path_from_child_collection(tree.field)
        return tree

    def _refine_sort_clause(self, clause: PlainSortClause):
        return PlainSortClause(field=self.path_from_child_collection(clause["field"]), ascending=clause["ascending"])

    async def refine_filter(self, filter: Optional[PaginatedFilter]) -> Optional[PaginatedFilter]:
        if filter:
            overrided: PaginatedFilterComponent = {}
            if filter.condition_tree:
                overrided["condition_tree"] = filter.condition_tree.replace(self._refine_leaf_tree)
            if filter.sort:
                overrided["sort"] = filter.sort.replace_clauses(self._refine_sort_clause)
            filter.override(overrided)
        return filter

    def record_to_child_collection(self, record: RecordsDataAlias) -> RecordsDataAlias:
        child_record: RecordsDataAlias = {}
        for field_name, value in record.items():
            child_record[self.to_child_collection.get(field_name, field_name)] = value
        return child_record

    def record_from_child_collection(self, record: RecordsDataAlias) -> RecordsDataAlias:
        new_record: RecordsDataAlias = {}

        for field_name, value in record.items():
            new_field_name = self.from_child_collection.get(field_name, field_name)
            schema = self.schema["fields"][new_field_name]
            if is_column(schema) or value is None:
                new_record[new_field_name] = value
            elif is_many_to_many(schema) or is_many_to_one(schema) or is_one_to_many(schema) or is_one_to_one(schema):
                relation = self.datasource.get_collection(schema["foreign_collection"])
                new_record[new_field_name] = relation.record_from_child_collection(value)
        return new_record

    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        records = await super().create([self.record_to_child_collection(d) for d in data])
        return [self.record_from_child_collection(record) for record in records]

    def path_from_child_collection(self, child_path: str) -> str:
        field, related_field = child_path.split(":")
        self_field = self.from_child_collection.get(field, field)
        if related_field:
            schema = self.schema["fields"][self_field]
            if is_many_to_many(schema) or is_one_to_many(schema) or is_one_to_one(schema) or is_many_to_one(schema):
                relation = self.datasource.get_collection(schema["foreign_collection"])
                return f"{self_field}:{relation.path_from_child_collection(related_field)}"
            else:
                raise RenameCollectionException(f"The field {self_field} is not a relation")
        return self_field

    def path_to_child_collection(self, path: str) -> str:
        field_name, related_field = path.split(":")
        if related_field:
            schema = self.schema["fields"][field_name]
            if is_many_to_many(schema) or is_one_to_many(schema) or is_one_to_one(schema) or is_many_to_one(schema):
                relation = self.datasource.get_collection(schema["foreign_collection"])
                child_field = self.to_child_collection.get(field_name, field_name)
                return f"{child_field}:{relation.path_to_child_collection(related_field)}"
            else:
                raise RenameCollectionException(f"The field {field_name} is not a relation")
        return self.to_child_collection.get(field_name, field_name)

    def _field_replacer(self, field: str) -> str:
        return self.path_to_child_collection(field)

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        child_projection = projection.replace(self._field_replacer)
        records = await super().list(filter, child_projection)
        return [self.record_from_child_collection(record) for record in records]

    async def update(self, filter: PaginatedFilter, patch: RecordsDataAlias) -> None:
        return await super().update(filter, self.record_to_child_collection(patch))

    def _build_group_aggregate(self, row: AggregateResult) -> Dict[str, Any]:
        group: Dict[str, Any] = {}
        for path, value in row["group"]:
            group[self.path_from_child_collection(path)] = value
        return group

    async def aggregate(
        self, filter: PaginatedFilter, aggregation: Aggregation, limit: Optional[int]
    ) -> List[AggregateResult]:
        rows = await super().aggregate(
            filter,
            aggregation.replace_fields(self._field_replacer),
            limit,
        )
        return [AggregateResult(value=row["value"], group=self._build_group_aggregate(row)) for row in rows]
