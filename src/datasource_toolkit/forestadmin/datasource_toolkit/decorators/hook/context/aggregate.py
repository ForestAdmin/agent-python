from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class HookBeforeAggregateContext(HookContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: Filter,
        aggregation: Aggregation,
        limit: Optional[int] = None,
    ):
        super().__init__(collection, caller)
        self.filter = filter_
        self.aggregation = aggregation
        self.limit = limit


class HookAfterAggregateContext(HookBeforeAggregateContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: Filter,
        aggregation: Aggregation,
        aggregate_result: List[AggregateResult],
        limit: Optional[int] = None,
    ):
        super().__init__(collection, caller, filter_, aggregation, limit)
        self.aggregate_result = aggregate_result
