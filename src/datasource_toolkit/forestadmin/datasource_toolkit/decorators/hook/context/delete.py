from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class HookBeforeDeleteContext(HookContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        filter_: Filter,
    ):
        super().__init__(collection, caller)
        self.filter = filter_


class HookAfterDeleteContext(HookBeforeDeleteContext):
    pass
