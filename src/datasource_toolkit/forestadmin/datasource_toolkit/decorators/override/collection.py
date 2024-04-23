from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.override.context import (
    CreateOverrideCustomizationContext,
    DeleteOverrideCustomizationContext,
    UpdateOverrideCustomizationContext,
)
from forestadmin.datasource_toolkit.decorators.override.types import (
    CreateOverrideHandler,
    DeleteOverrideHandler,
    UpdateOverrideHandler,
)
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


class OverrideCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._create_handler: Optional[CreateOverrideHandler] = None
        self._update_handler: Optional[UpdateOverrideHandler] = None
        self._delete_handler: Optional[DeleteOverrideHandler] = None

    def add_create_handler(self, handler: CreateOverrideHandler):
        self._create_handler = handler

    def add_update_handler(self, handler: UpdateOverrideHandler):
        self._update_handler = handler

    def add_delete_handler(self, handler: DeleteOverrideHandler):
        self._delete_handler = handler

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        if self._create_handler is not None:
            context = CreateOverrideCustomizationContext(self.child_collection, caller, data)
            return await call_user_function(self._create_handler, context)
        return await super().create(caller, data)

    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        if self._update_handler is not None:
            context = UpdateOverrideCustomizationContext(self.child_collection, caller, _filter, patch)
            return await call_user_function(self._update_handler, context)
        return await super().update(caller, _filter, patch)

    async def delete(self, caller: User, _filter: Optional[Filter]) -> None:
        if self._delete_handler is not None:
            context = DeleteOverrideCustomizationContext(self.child_collection, caller, _filter)
            return await call_user_function(self._delete_handler, context)
        return await super().delete(caller, _filter)
