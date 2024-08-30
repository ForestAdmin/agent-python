import enum
import sys
from functools import reduce
from typing import Any, Callable, List, Literal, Union

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    AsyncReplacerAlias,
    CallbackAlias,
    ConditionTree,
    ConditionTreeComponent,
    ConditionTreeException,
    ReplacerAlias,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf, LeafComponents
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils import removeprefix
from typing_extensions import Self, TypeGuard


class Aggregator(enum.Enum):
    OR = "or"
    AND = "and"


LiteralAggregator = Literal["or", "and"]


class BranchComponents(ConditionTreeComponent):
    aggregator: LiteralAggregator
    conditions: List[Union["BranchComponents", LeafComponents]]


def is_branch_component(tree: Any) -> TypeGuard[BranchComponents]:
    return isinstance(tree, dict) and "aggregator" in tree.keys() and "conditions" in tree.keys()


class ConditionTreeBranch(ConditionTree):
    def __init__(self, aggregator: Union[Aggregator, LiteralAggregator], conditions: List[ConditionTree]):
        super().__init__()
        self.aggregator = Aggregator(aggregator)
        self.conditions = conditions

    def __repr__(self):
        return f"{self.aggregator}[{self.conditions}]"

    def __eq__(self: Self, obj: Self) -> bool:  # type: ignore
        return (
            self.__class__ == obj.__class__ and self.aggregator == obj.aggregator and self.conditions == obj.conditions
        )

    @property
    def projection(self) -> Projection:
        def reducer(memo: Projection, condition: ConditionTree):
            return memo.union(condition.projection)

        return reduce(reducer, self.conditions, Projection())

    def inverse(self) -> "ConditionTree":
        aggregator = Aggregator.OR
        if self.aggregator == Aggregator.OR:
            aggregator = Aggregator.AND
        return ConditionTreeBranch(aggregator, [condition.inverse() for condition in self.conditions])

    def match(self, record: RecordsDataAlias, collection: Collection, timezone: zoneinfo.ZoneInfo) -> bool:
        meth = all
        if self.aggregator == Aggregator.OR:
            meth = any
        return meth([condition.match(record, collection, timezone) for condition in self.conditions])

    def some_leaf(self, handler: Callable[["ConditionTreeLeaf"], bool]) -> bool:  # noqa:F821
        for condition in self.conditions:
            handler_res = handler(condition)  # type: ignore
            if handler_res is True:
                return True
        return False

    def apply(self, handler: "CallbackAlias") -> None:
        for condition in self.conditions:
            condition.apply(handler)

    def replace(self, handler: "ReplacerAlias") -> "ConditionTree":
        return ConditionTreeBranch(
            self.aggregator,
            [condition.replace(handler) for condition in self.conditions],
        )

    async def replace_async(self, handler: "AsyncReplacerAlias") -> "ConditionTree":
        return ConditionTreeBranch(
            self.aggregator,
            [await condition.replace_async(handler) for condition in self.conditions],
        )

    def nest(self, prefix: str) -> "ConditionTreeBranch":
        return ConditionTreeBranch(self.aggregator, [condition.nest(prefix) for condition in self.conditions])

    def _get_prefix(self) -> str:
        prefixes: List[str] = []

        def __split(tree: ConditionTree) -> None:
            if isinstance(tree, ConditionTreeLeaf) and ":" in tree.field:
                prefixes.append(tree.field.split(":")[0])

        self.apply(__split)

        if len(set(prefixes)) != 1:
            raise ConditionTreeException("Cannot unnest condition tree")
        return prefixes[0]

    def _remove_prefix(self, prefix: str) -> ConditionTree:
        def __rename(tree: ConditionTree) -> ConditionTree:
            if isinstance(tree, ConditionTreeLeaf):
                return tree.replace_field(removeprefix(tree.field, f"{prefix}:"))
            return tree

        return self.replace(__rename)

    def unnest(self) -> ConditionTree:
        prefix = self._get_prefix()
        return self._remove_prefix(prefix)

    def to_plain_object(self) -> BranchComponents:  # type: ignore
        return BranchComponents(
            aggregator=self.aggregator.value,
            conditions=[condition.to_plain_object() for condition in self.conditions],  # type: ignore
        )

    def for_each_leaf(self, handler: Callable[[ConditionTreeLeaf], None]):
        for leaf in self.conditions:
            leaf.for_each_leaf(handler)
