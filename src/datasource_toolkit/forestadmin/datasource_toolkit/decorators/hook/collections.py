from typing import Dict, List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.hook.context.aggregate import (
    HookAfterAggregateContext,
    HookBeforeAggregateContext,
)
from forestadmin.datasource_toolkit.decorators.hook.context.create import (
    HookAfterCreateContext,
    HookBeforeCreateContext,
)
from forestadmin.datasource_toolkit.decorators.hook.context.delete import (
    HookAfterDeleteContext,
    HookBeforeDeleteContext,
)
from forestadmin.datasource_toolkit.decorators.hook.context.list import HookAfterListContext, HookBeforeListContext
from forestadmin.datasource_toolkit.decorators.hook.context.update import (
    HookAfterUpdateContext,
    HookBeforeUpdateContext,
)
from forestadmin.datasource_toolkit.decorators.hook.hooks import Hooks
from forestadmin.datasource_toolkit.decorators.hook.types import CrudMethod, HookHandler, Position
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class CollectionHookDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._hooks: Dict[CrudMethod, Hooks] = {
            "List": Hooks(),
            "Create": Hooks(),
            "Update": Hooks(),
            "Delete": Hooks(),
            "Aggregate": Hooks(),
        }

    def add_hook(self, position: Position, type_: CrudMethod, handler: HookHandler):
        self._hooks[type_].add_handler(position, handler)

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        before_context = HookBeforeListContext(self.child_collection, caller, _filter, projection)
        await self._hooks["List"].execute_before(before_context)

        records = await self.child_collection.list(caller, _filter, projection)

        after_context = HookAfterListContext(self.child_collection, caller, _filter, projection, records)
        await self._hooks["List"].execute_after(after_context)

        return records

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        before_context = HookBeforeCreateContext(self.child_collection, caller, data)
        await self._hooks["Create"].execute_before(before_context)

        records = await self.child_collection.create(caller, data)

        after_context = HookAfterCreateContext(self.child_collection, caller, data, records)
        await self._hooks["Create"].execute_after(after_context)

        return records

    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        before_context = HookBeforeUpdateContext(self.child_collection, caller, _filter, patch)
        await self._hooks["Update"].execute_before(before_context)

        await self.child_collection.update(caller, _filter, patch)

        after_context = HookAfterUpdateContext(self.child_collection, caller, _filter, patch)
        await self._hooks["Update"].execute_after(after_context)

    async def delete(self, caller: User, _filter: Optional[Filter]) -> None:
        before_context = HookBeforeDeleteContext(self.child_collection, caller, _filter)
        await self._hooks["Delete"].execute_before(before_context)

        await self.child_collection.delete(caller, _filter)

        after_context = HookAfterDeleteContext(self.child_collection, caller, _filter)
        await self._hooks["Delete"].execute_after(after_context)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        before_context = HookBeforeAggregateContext(self.child_collection, caller, _filter, aggregation, limit)
        await self._hooks["Aggregate"].execute_before(before_context)

        aggregate_result = await self.child_collection.aggregate(caller, _filter, aggregation, limit)

        after_context = HookAfterAggregateContext(
            self.child_collection, caller, _filter, aggregation, aggregate_result, limit
        )
        await self._hooks["Aggregate"].execute_after(after_context)

        return aggregate_result
