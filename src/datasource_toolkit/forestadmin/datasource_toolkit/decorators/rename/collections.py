from typing import Any, Callable, Dict, List, Optional, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class RenameCollectionException(DatasourceToolkitException):
    pass


class RenameMixin:

    datasource: property
    mark_schema_as_dirty: Callable[..., None]

    def __init__(self, *args: Any, **kwargs: Any):
        super(RenameMixin, self).__init__(*args, **kwargs)
        self._to_child_collection: Dict[str, str] = {}
        self._from_child_collection: Dict[str, str] = {}

    def rename_field(self, current_name: str, new_name: str):
        schema = self.schema
        if current_name not in schema["fields"]:
            raise RenameCollectionException(f"No such field {current_name}")

        initial_name = current_name
        if current_name in self._to_child_collection:
            child_name = self._to_child_collection[current_name]
            del self._to_child_collection[current_name]
            del self._from_child_collection[child_name]
            initial_name = child_name

        if initial_name != new_name:
            self._from_child_collection[initial_name] = new_name
            self._to_child_collection[new_name] = initial_name
        self.mark_schema_as_dirty()

    async def _refine_filter(
        self, filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        def computed_fields(tree: ConditionTree) -> ConditionTree:
            if isinstance(tree, ConditionTreeLeaf):
                tree.field = self._path_to_child_collection(tree.field)
            return tree

        filter = await super()._refine_filter(filter)  # type: ignore
        if filter and filter.condition_tree:
            filter = filter.override({"condition_tree": filter.condition_tree.replace(computed_fields)})  # type: ignore
        return filter

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        child_projection = projection.replace(lambda field_name: self._path_to_child_collection(field_name))
        records: List[RecordsDataAlias] = await super(RenameMixin, self).list(filter, child_projection)  # type: ignore
        return [self._record_from_child_collection(record) for record in records]

    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        records: List[RecordsDataAlias] = await super().create(  # type: ignore
            [self._record_to_child_collection(d) for d in data]
        )
        return [self._record_from_child_collection(record) for record in records]

    async def update(self, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        refined_patch = self._record_to_child_collection(patch)
        return await super(RenameMixin, self).update(filter, refined_patch)  # type: ignore

    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        rows: List[AggregateResult] = await super().aggregate(  # type: ignore
            filter, aggregation.replace_fields(lambda name: self._path_to_child_collection(name)), limit
        )
        return [AggregateResult(value=row["value"], group=self._build_group_aggregate(row)) for row in rows]

    def _build_group_aggregate(self, row: AggregateResult) -> Dict[str, Any]:
        group: Dict[str, Any] = {}
        for path, value in row["group"].items():
            group[self._path_from_child_collection(path)] = value
        return group

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(RenameMixin, self).schema  # type: ignore

        new_fields_schema = {}
        datasource = cast(Datasource[BoundCollection], self.datasource)
        for old_field_name, field_schema in schema["fields"].items():
            if is_many_to_many(field_schema):
                field_schema["foreign_key"] = self._from_child_collection.get(
                    field_schema["foreign_key"], field_schema["foreign_key"]
                )
            elif is_one_to_many(field_schema) or is_one_to_one(field_schema):
                relation = datasource.get_collection(field_schema["foreign_collection"])
                relation = cast("RenameMixin", relation)
                field_schema["origin_key"] = relation._from_child_collection.get(
                    field_schema["origin_key"], field_schema["origin_key"]
                )
            elif is_many_to_many(field_schema):
                through = datasource.get_collection(field_schema["through_collection"])
                through = cast("RenameMixin", through)
                field_schema["foreign_key"] = through._from_child_collection.get(
                    field_schema["foreign_key"], field_schema["foreign_key"]
                )
                field_schema["origin_key"] = through._from_child_collection.get(
                    field_schema["origin_key"], field_schema["origin_key"]
                )

            new_fields_schema[self._from_child_collection.get(old_field_name, old_field_name)] = field_schema
        schema["fields"] = new_fields_schema
        return schema

    def _path_from_child_collection(self, child_path: str) -> str:
        datasource = cast(Datasource[BoundCollection], self.datasource)
        field, related_field = child_path, None
        if ":" in child_path:
            field, *related_field = child_path.split(":")
        self_field = self._from_child_collection.get(field, field)
        if related_field:
            schema = self.schema["fields"][self_field]
            if is_many_to_many(schema) or is_one_to_many(schema) or is_one_to_one(schema) or is_many_to_one(schema):
                relation = datasource.get_collection(schema["foreign_collection"])
                relation = cast("RenameMixin", relation)
                return f"{self_field}:{relation._path_from_child_collection(':'.join(related_field))}"
            else:
                raise RenameCollectionException(f"The field {self_field} is not a relation")
        return self_field

    def _refine_leaf_tree(self, tree: ConditionTree) -> ConditionTree:
        if isinstance(tree, ConditionTreeLeaf):
            tree.field = self._path_to_child_collection(tree.field)
        return tree

    def _refine_sort_clause(self, clause: PlainSortClause):
        return PlainSortClause(field=self._path_to_child_collection(clause["field"]), ascending=clause["ascending"])

    def _record_to_child_collection(self, record: RecordsDataAlias) -> RecordsDataAlias:
        child_record: RecordsDataAlias = {}
        for field_name, value in record.items():
            child_record[self._to_child_collection.get(field_name, field_name)] = value
        return child_record

    def _record_from_child_collection(self, record: RecordsDataAlias) -> RecordsDataAlias:
        new_record: RecordsDataAlias = {}
        datasource = cast(Datasource[BoundCollection], self.datasource)
        for field_name, value in record.items():
            new_field_name = self._from_child_collection.get(field_name, field_name)
            new_field_name, *_ = new_field_name.split(":")
            schema = self.schema["fields"][new_field_name]
            if is_column(schema) or value is None:
                new_record[new_field_name] = value
            elif is_many_to_many(schema) or is_many_to_one(schema) or is_one_to_many(schema) or is_one_to_one(schema):
                relation = datasource.get_collection(schema["foreign_collection"])
                relation = cast("RenameMixin", relation)
                new_record[new_field_name] = relation._record_from_child_collection(value)
        return new_record

    def _path_to_child_collection(self, path: str) -> str:
        datasource = cast(Datasource[BoundCollection], self.datasource)
        field_name, related_field = path, None
        if ":" in path:
            field_name, *related_field = path.split(":")
            related_field = ":".join(related_field)
        if related_field:
            schema = self.schema["fields"][field_name]
            if is_many_to_many(schema) or is_one_to_many(schema) or is_one_to_one(schema) or is_many_to_one(schema):
                relation = datasource.get_collection(schema["foreign_collection"])
                relation = cast("RenameMixin", relation)
                child_field = self._to_child_collection.get(field_name, field_name)
                return f"{child_field}:{relation._path_to_child_collection(related_field)}"
            else:
                raise RenameCollectionException(f"The field {field_name} is not a relation")
        return self._to_child_collection.get(field_name, field_name)
