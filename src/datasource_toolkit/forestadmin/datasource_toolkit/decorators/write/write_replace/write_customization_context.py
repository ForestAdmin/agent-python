from types import MappingProxyType
from typing import Literal, Optional, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class WriteCustomizationContext(CollectionCustomizationContext):
    def __init__(
        self,
        collection: Collection,
        caller: User,
        action: Union[Literal["update"], Literal["create"]],
        record: RecordsDataAlias,
        filter_: Optional[Filter] = None,
    ):
        self.action = action
        self.filter = filter_
        self.record = MappingProxyType({**record})
        super().__init__(collection, caller)
