from typing import Any, Dict, Optional, Set, Union

from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, Operator, is_column
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence import ConditionTreeEquivalent
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.operators import ALL_OPERATORS
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils


class OperatorReplaceMixin:
    def __init__(self, *args: Any, **kwargs: Any):
        super(OperatorReplaceMixin, self).__init__(*args, **kwargs)
        self._allowed_operator: Dict[str, Set[Operator]] = {}

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(OperatorReplaceMixin, self).schema  # type: ignore
        fields: Dict[str, FieldAlias] = {}

        for name, field_schema in schema["fields"].items():
            if is_column(field_schema) and name not in self._allowed_operator:
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

        return {**schema, "fields": fields}

    async def _refine_filter(
        self, filter: Union[Optional[PaginatedFilter], Optional[Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        def refine_equivalent_tree(tree: ConditionTree) -> ConditionTree:
            if isinstance(tree, ConditionTreeLeaf):
                field_schema = CollectionUtils.get_field_schema(self, tree.field)  # type: ignore
                if is_column(field_schema):
                    res = ConditionTreeEquivalent.get_equivalent_tree(
                        tree,
                        self._allowed_operator[tree.field],
                        field_schema["column_type"],
                        filter.timezone,  # type: ignore
                    )
                    if res:
                        return res
            return tree

        filter = await super()._refine_filter(filter)  # type: ignore
        if filter and filter.condition_tree:
            filter = filter.override({"condition_tree": filter.condition_tree.replace(refine_equivalent_tree)})
        return filter
