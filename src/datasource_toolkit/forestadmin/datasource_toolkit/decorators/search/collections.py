from typing import Dict, List, Optional, Tuple, Union, cast

from typing_extensions import TypeGuard

from forestadmin.datasource_toolkit.decorators.collections import CollectionDecorator
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
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    CollectionSchema,
    Datasource,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import (
    PaginatedFilter,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter


class SearchCollectionDecorator(CollectionDecorator):

    TYPE_TO_OPERATOR: Dict[ColumnAlias, Operator] = {
        PrimitiveType.STRING: Operator.CONTAINS,
        PrimitiveType.ENUM: Operator.EQUAL,
        PrimitiveType.NUMBER: Operator.EQUAL,
        PrimitiveType.UUID: Operator.EQUAL,
    }

    def _refine_schema(self, child_schema: CollectionSchema) -> CollectionSchema:
        schema = child_schema.copy()
        schema["searchable"] = True
        return schema

    async def refine_filter(
        self, filter: Optional[Union[PaginatedFilter, Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:

        if not filter or not filter.search or self.child_collection.schema["searchable"]:
            return filter

        if SearchCollectionDecorator.check_empty_string(filter.search):
            return filter.override({"search": None})

        searchable_fields = SearchCollectionDecorator.get_searchable_fields(
            self.child_collection.schema, self.child_collection.datasource, filter.search_extended or False
        )

        conditions: List[ConditionTree] = []
        for field, schema in searchable_fields:
            condition = SearchCollectionDecorator.build_condition(field, schema, filter.search)
            if condition:
                conditions.append(condition)
        trees = [ConditionTreeFactory.union(conditions)]
        if filter.condition_tree:
            trees.append(filter.condition_tree)
        return filter.override({"condition_tree": ConditionTreeFactory.intersect(trees), "search": None})

    @classmethod
    def build_condition(cls, field: str, schema: Column, search: str):
        condition: Optional[ConditionTree] = None
        type = cast(PrimitiveType, schema["column_type"])
        enum_values = schema["enum_values"] or []
        value: Union[int, float, str] = search
        if schema["column_type"] == PrimitiveType.NUMBER:
            try:
                value = int(search)
            except ValueError:
                value = float(search)
        search_type = TypeGetter.get(value, type)
        if cls.is_valid_enum(enum_values, search, type) or search_type in [PrimitiveType.NUMBER, PrimitiveType.UUID]:
            condition = ConditionTreeLeaf(field, Operator.EQUAL, value)
        elif search_type == PrimitiveType.STRING:
            condition = ConditionTreeLeaf(field, Operator.CONTAINS, value)

        return condition

    @staticmethod
    def is_valid_enum(enum_values: List[str], search: str, search_type: PrimitiveType) -> bool:
        values = [enum_value.lower() for enum_value in enum_values]
        search = search.lower().strip()
        return search_type == PrimitiveType.ENUM and search in values

    @classmethod
    def get_searchable_fields(
        cls, schema: CollectionSchema, datasource: Datasource[CollectionDecorator], search_extended: bool
    ) -> List[Tuple[str, Column]]:
        fields = list(schema["fields"].items())
        if search_extended:
            fields.extend(cls.get_deep_fields(datasource, fields))
        return [(field_name, schema) for field_name, schema in fields if cls.is_searchable(schema)]

    @classmethod
    def is_searchable(cls, schema: FieldAlias) -> TypeGuard[Column]:
        filter_operators = schema.get("filter_operators") or set()
        if is_column(schema):
            try:
                return cls.TYPE_TO_OPERATOR[schema["column_type"]] in filter_operators
            except KeyError:
                return False
        return False

    @staticmethod
    def get_deep_fields(datasource: Datasource[CollectionDecorator], fields: List[Tuple[str, FieldAlias]]):
        deep_fields: List[Tuple[str, FieldAlias]] = []
        for name, field in fields:
            if is_many_to_one(field) or is_one_to_one(field):
                related = datasource.get_collection(field["foreign_collection"])
                for deep_name, deep_schema in related.schema["fields"].items():
                    deep_fields.append((f"{name}:{deep_name}", deep_schema))
        return deep_fields

    @staticmethod
    def check_empty_string(search: str) -> bool:
        return len(search.strip()) == 0
