from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class CreateOverrideCustomizationContext(CollectionCustomizationContext):
    def __init__(self, collection: Collection, caller: User, data: List[RecordsDataAlias]):
        self.data: List[RecordsDataAlias] = [{**d} for d in data]
        super().__init__(collection, caller)


class UpdateOverrideCustomizationContext(CollectionCustomizationContext):
    def __init__(self, collection: Collection, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias):
        self.patch: RecordsDataAlias = {**patch}
        self.filter: Optional[Filter] = filter_
        super().__init__(collection, caller)


class DeleteOverrideCustomizationContext(CollectionCustomizationContext):
    def __init__(self, collection: Collection, caller: User, filter_: Optional[Filter]):
        self.filter: Optional[Filter] = filter_
        super().__init__(collection, caller)
