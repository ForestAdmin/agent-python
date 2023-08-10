from typing import List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class HookBeforeCreateContext(HookContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        data: List[RecordsDataAlias],
    ):
        super().__init__(collection, caller)
        self.data = data


class HookAfterCreateContext(HookBeforeCreateContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        data: List[RecordsDataAlias],
        records: List[RecordsDataAlias],
    ):
        super().__init__(collection, caller, data)
        self.records = records
