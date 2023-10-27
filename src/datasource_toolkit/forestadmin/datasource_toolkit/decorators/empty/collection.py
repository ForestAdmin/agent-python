from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class EmptyCollectionDecorator(CollectionDecorator):
    async def list(self, caller: User, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        if not self._returns_empty_set(filter.condition_tree):
            return await super().list(caller, filter, projection)

        return []

    async def update(self, caller: User, filter: PaginatedFilter, patch: RecordsDataAlias) -> List[RecordsDataAlias]:
        if not self._returns_empty_set(filter.condition_tree):
            return await super().update(caller, filter, patch)

        return None

    async def delete(self, caller: User, filter: Optional[Filter]) -> None:
        if not self._returns_empty_set(filter.condition_tree):
            return await super().delete(caller, filter)

        return None

    async def aggregate(
        self, caller: User, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        if not self._returns_empty_set(filter.condition_tree):
            return await super().aggregate(caller, filter, aggregation, limit)

        return []

    def _returns_empty_set(self, tree: ConditionTree) -> bool:
        if isinstance(tree, ConditionTreeLeaf):
            return self._leaf_returns_empty_set(tree)

        if isinstance(tree, ConditionTreeBranch) and tree.aggregator == Aggregator.OR:
            return self._or_returns_empty_set(tree.conditions)

        if isinstance(tree, ConditionTreeBranch) and tree.aggregator == Aggregator.AND:
            return self._and_returns_empty_set(tree.conditions)

        return False

    def _leaf_returns_empty_set(self, leaf: ConditionTreeLeaf) -> bool:
        # Empty 'in` always return zero records.
        return leaf.operator == Operator.IN and len(leaf.value or []) == 0

    def _or_returns_empty_set(self, conditions: List[ConditionTree]) -> bool:
        # Or return no records when
        # - they have no conditions
        # - they have only conditions which return zero records.
        return len(conditions) == 0 or all(self._returns_empty_set(c) for c in conditions)

    def _and_returns_empty_set(self, conditions: List[ConditionTree]) -> bool:
        # There is a leaf which returns zero records
        for condition in conditions:
            if self._returns_empty_set(condition):
                return True

        # Scans for mutually exclusive conditions
        # (this a naive implementation, it will miss many occurrences)
        values_by_field = {}
        leafs = [condition for condition in conditions if isinstance(condition, ConditionTreeLeaf)]

        for leaf in leafs:
            if leaf.field not in values_by_field and leaf.operator == Operator.EQUAL:
                values_by_field[leaf.field] = [leaf.value]

            elif leaf.field not in values_by_field and leaf.operator == Operator.IN:
                values_by_field[leaf.field] = leaf.value or []

            elif leaf.field in values_by_field and leaf.operator == Operator.EQUAL:
                values_by_field[leaf.field] = [leaf.value] if leaf.value in values_by_field[leaf.field] else []

            elif leaf.field in values_by_field and leaf.operator == Operator.IN:
                values_by_field[leaf.field] = [value for value in values_by_field[leaf.field] if value in leaf.value]

        for value in values_by_field.values():
            if len(value) == 0:
                return True
        return False
