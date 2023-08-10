from typing import List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class HookBeforeListContext(HookContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: PaginatedFilter,
        projection: Projection,
    ):
        super().__init__(collection, caller)
        self.filter = filter_
        self.projection = projection


class HookAfterListContext(HookBeforeListContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: PaginatedFilter,
        projection: Projection,
        records: List[RecordsDataAlias],
    ):
        super().__init__(collection, caller, filter_, projection)
        self.records = records
