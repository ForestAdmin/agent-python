from typing import Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class HookBeforeUpdateContext(HookContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: Optional[Filter],
        patch: RecordsDataAlias,
    ):
        super().__init__(collection, caller)
        self.filter = filter_
        self.patch = patch


class HookAfterUpdateContext(HookBeforeUpdateContext):
    pass
