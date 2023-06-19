from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.context.relaxed_wrappers.collection import RelaxedCollection
from forestadmin.datasource_toolkit.interfaces.collections import Collection


class CollectionCustomizationContext(AgentCustomizationContext):
    def __init__(self, collection: Collection, caller: User):
        super().__init__(collection.datasource, caller)
        self._collection = collection

    @property
    def collection(self) -> RelaxedCollection:
        return RelaxedCollection(self._collection)
