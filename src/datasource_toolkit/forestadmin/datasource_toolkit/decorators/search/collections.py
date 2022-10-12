from typing import Dict, List, Optional, Tuple, Union, cast

from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ColumnAlias,
    FieldAlias,
    Operator,
    PrimitiveType,
    is_column,
    is_many_to_one,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter
from typing_extensions import TypeGuard


class SearchMixin:  # type: ignore

    datasource: property

    TYPE_TO_OPERATOR: Dict[ColumnAlias, Operator] = {
        PrimitiveType.STRING: Operator.CONTAINS,
        PrimitiveType.ENUM: Operator.EQUAL,
        PrimitiveType.NUMBER: Operator.EQUAL,
        PrimitiveType.UUID: Operator.EQUAL,
    }

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(SearchMixin, self).schema  # type: ignore
        schema["searchable"] = True
        return schema

    async def _refine_filter(
        self, filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        filter = cast(PaginatedFilter, await super()._refine_filter(filter))  # type: ignore
        if not filter or not filter.search:
            return filter

        if self._is_empty_string(filter.search):
            return filter.override({"search": None})

        searchable_fields = self._get_searchable_fields(self.schema, filter.search_extended or False)

        conditions: List[ConditionTree] = []
        for field, schema in searchable_fields:
            try:
                condition = self._build_condition(field, schema, filter.search)
            except ValueError:
                condition = None
            if condition:
                conditions.append(condition)
        trees: List[ConditionTree] = []
        if conditions:
            trees.append(ConditionTreeFactory.union(conditions))
        if filter.condition_tree:
            trees.append(filter.condition_tree)

        if trees:
            return filter.override({"condition_tree": ConditionTreeFactory.intersect(trees), "search": None})

        raise Exception("filter search type not matching any fields's type")

    def _build_condition(self, field: str, schema: Column, search: str) -> Optional[ConditionTree]:
        condition: Optional[ConditionTree] = None
        type_ = cast(PrimitiveType, schema["column_type"])
        enum_values = schema["enum_values"] or []
        value: Union[int, float, str] = search

        if schema["column_type"] == PrimitiveType.NUMBER:
            try:
                value = int(search)
            except ValueError:
                value = float(search)

        search_type = TypeGetter.get(value, type_)

        if self._is_valid_enum(enum_values, search, type_) or search_type in [PrimitiveType.NUMBER, PrimitiveType.UUID]:
            condition = ConditionTreeLeaf(field, Operator.EQUAL, value)
        elif search_type == PrimitiveType.STRING:
            condition = ConditionTreeLeaf(field, Operator.CONTAINS, value)

        return condition

    def _is_valid_enum(self, enum_values: List[str], search: str, search_type: PrimitiveType) -> bool:
        values = [enum_value.lower() for enum_value in enum_values]
        search = search.lower().strip()
        return search_type == PrimitiveType.ENUM and search in values

    def _get_searchable_fields(self, schema: CollectionSchema, search_extended: bool) -> List[Tuple[str, Column]]:
        fields = list(schema["fields"].items())
        if search_extended:
            fields.extend(self._get_deep_fields(fields))
        return [(field_name, schema) for field_name, schema in fields if self._is_searchable(schema)]

    def _is_searchable(self, schema: FieldAlias) -> TypeGuard[Column]:
        filter_operators = schema.get("filter_operators") or set()
        if is_column(schema):
            try:
                return self.TYPE_TO_OPERATOR[schema["column_type"]] in filter_operators
            except KeyError:
                return False
        return False

    def _get_deep_fields(self, fields: List[Tuple[str, FieldAlias]]):
        deep_fields: List[Tuple[str, FieldAlias]] = []
        for name, field in fields:
            if is_many_to_one(field) or is_one_to_one(field):
                related = cast(Datasource[BoundCollection], self.datasource).get_collection(field["foreign_collection"])
                for deep_name, deep_schema in related.schema["fields"].items():
                    deep_fields.append((f"{name}:{deep_name}", deep_schema))
        return deep_fields

    def _is_empty_string(self, search: str) -> bool:
        return len(search.strip()) == 0
