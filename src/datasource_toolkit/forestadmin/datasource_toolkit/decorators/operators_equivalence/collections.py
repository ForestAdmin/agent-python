from typing import Any, Dict, Optional, Set, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, Operator, is_column
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence import ConditionTreeEquivalent
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.operators import ALL_OPERATORS
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils


class OperatorEquivalenceCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._allowed_operator: Dict[str, Set[Operator]] = {}
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields: Dict[str, FieldAlias] = {}

        for name, field_schema in sub_schema["fields"].items():
            if is_column(field_schema):
                if name not in self._allowed_operator:
                    self._allowed_operator[name] = field_schema.get("filter_operators") or set()

                new_operators: Set[Operator] = set(
                    filter(
                        lambda operator: ConditionTreeEquivalent.has_equivalent_tree(
                            operator,
                            field_schema.get("filter_operators", []),  # type: ignore
                            field_schema.get("column_type"),  # type: ignore
                        ),
                        ALL_OPERATORS,
                    )
                )
                fields[name] = {**field_schema, "filter_operators": new_operators}  # type: ignore
            else:
                fields[name] = field_schema
        sub_schema = {**sub_schema, "fields": fields}
        return sub_schema

    async def _refine_filter(
        self, caller: User, _filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        def refine_equivalent_tree(tree: ConditionTree) -> ConditionTree:
            if isinstance(tree, ConditionTreeLeaf):
                collection = self
                field = tree.field
                if ":" in tree.field:
                    parent_name, field = tree.field.split(":")
                    parent_field = self.get_field(parent_name)
                    collection = self.datasource.get_collection(parent_field["foreign_collection"])  # type: ignore
                field_schema = CollectionUtils.get_field_schema(collection, field)  # type: ignore
                if is_column(field_schema):
                    res = ConditionTreeEquivalent.get_equivalent_tree(
                        tree,
                        collection._allowed_operator[field],
                        field_schema["column_type"],
                        _filter.timezone,  # type: ignore
                    )
                    if res:
                        return res
            return tree

        _filter = await super()._refine_filter(caller, _filter)  # type: ignore
        if _filter and _filter.condition_tree:
            _filter = _filter.override({"condition_tree": _filter.condition_tree.replace(refine_equivalent_tree)})
        return _filter
