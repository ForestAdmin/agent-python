from ast import literal_eval
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ColumnAlias,
    Operator,
    PrimitiveType,
    is_column,
    is_many_to_one,
    is_one_to_one,
    is_valid_uuid,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

SearchDefinition = Callable[[Any, bool, CollectionCustomizationContext], ConditionTree]


class SearchCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource[BoundCollection]):
        super().__init__(collection, datasource)
        self._replacer: SearchDefinition = None

    def replace_search(self, replacer: SearchDefinition):
        self._replacer = replacer

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        return {**sub_schema, "searchable": True}

    def _default_replacer(self, search: str, extended: bool) -> ConditionTree:
        searchable_fields = self._get_searchable_fields(self.child_collection, extended)
        conditions = [self._build_condition(name, field, search) for (name, field) in searchable_fields]

        return ConditionTreeFactory.union(conditions)

    async def _refine_filter(
        self, caller: User, _filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        # Search string is not significant
        if _filter.search is None or _filter.search.strip() == "":
            return _filter.override({"search": None})

        # Implement search ourselves
        if self._replacer or not self.child_collection.schema["searchable"]:
            context = CollectionCustomizationContext(self, caller)
            tree = self._default_replacer(_filter.search, _filter)

            if self._replacer is not None:
                tree = self._replacer(_filter.search, _filter.search_extended, context)
                if isinstance(tree, Awaitable):
                    tree = await tree

                if isinstance(tree, dict):
                    tree = ConditionTreeFactory.from_plain_object(tree)

            # Note that if no fields are searchable with the provided searchString, the conditions
            # array might be empty, which will create a condition returning zero records
            # (this is the desired behavior).
            return _filter.override(
                {"condition_tree": ConditionTreeFactory.intersect([_filter.condition_tree, tree]), "search": None}
            )

        # Let sub collection deal with the search
        return _filter

    def _build_condition(self, field: str, schema: Column, search: str) -> Union[ConditionTree, None]:
        if (
            schema["column_type"] == PrimitiveType.NUMBER
            and search.isnumeric()
            and Operator.EQUAL in schema.get("filter_operators", [])
        ):
            value = literal_eval(str(search))
            return ConditionTreeLeaf(field, Operator.EQUAL, value)

        if schema["column_type"] == PrimitiveType.ENUM and Operator.EQUAL in schema.get("filter_operators", []):
            search_value = self.lenient_find(schema["enum_values"], search)
            if search_value is not None:
                return ConditionTreeLeaf(field, Operator.EQUAL, search_value)

        if schema["column_type"] == PrimitiveType.STRING:
            support_icontains = False  # Operator.ICONTAINS in schema.get("filter_operators",[])
            support_contains = Operator.CONTAINS in schema.get("filter_operators", [])
            support_equal = Operator.EQUAL in schema.get("filter_operators", [])
            if support_icontains and not support_contains:
                pass  # operator = Operator.ICONTAINS
            elif support_contains:
                operator = Operator.CONTAINS
            elif support_equal:
                operator = Operator.EQUAL
            else:
                operator = None

            if operator:
                return ConditionTreeLeaf(field, operator, search)

        if (
            schema["column_type"] == PrimitiveType.UUID
            and is_valid_uuid(search)
            and Operator.EQUAL in schema.get("filter_operators", [])
        ):
            return ConditionTreeLeaf(field, Operator.EQUAL, search)

    def lenient_find(self, haystack: List[str], needle: str) -> Union[str, None]:
        for item in haystack:
            if needle.strip() == item or needle.strip().lower() == item.lower():
                return item
        return None

    def _get_searchable_fields(self, collection: Collection, extended: bool) -> List[Tuple[str, ColumnAlias]]:
        fields: List[Tuple[str, ColumnAlias]] = []

        for name, field in collection.schema["fields"].items():
            if is_column(field):
                fields.append((name, field))

            if extended and (is_many_to_one(field) or is_one_to_one(field)):
                related = collection.datasource.get_collection(field["foreign_collection"])

                for sub_name, sub_field in related.schema["fields"].items():
                    if is_column(sub_field):
                        fields.append((f"{name}:{sub_name}", sub_field))
        return fields
