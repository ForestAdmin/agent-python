import sys
from typing import Optional

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.context.relaxed_wrappers.collection import RelaxedCollection
from forestadmin.datasource_toolkit.interfaces.collections import Collection


class CollectionCustomizationContext(AgentCustomizationContext):
    def __init__(self, collection: Collection, timezone: Optional[zoneinfo.ZoneInfo] = None):
        super().__init__(collection.datasource, timezone)
        self._collection = collection

    @property
    def collection(self) -> RelaxedCollection:
        return RelaxedCollection(self._collection)
