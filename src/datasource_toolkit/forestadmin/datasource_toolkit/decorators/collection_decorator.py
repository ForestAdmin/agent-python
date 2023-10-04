from typing import Any, Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import CollectionException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class CollectionDecorator(Collection):
    def __init__(self, collection: Collection, datasource: Datasource[BoundCollection]):
        self.child_collection = collection
        self._datasource = datasource
        self._last_schema = None

        # When the child collection invalidates its schema, we also invalidate ours.
        # This is done like this, and not in the markSchemaAsDirty method, because we don't have
        # a reference to parent collections from children.
        if isinstance(self.child_collection, CollectionDecorator):
            child_mark_schema_as_dirty = self.child_collection.mark_schema_as_dirty

            def patched_mark_schema_as_dirty():
                # Call the original method (the child)
                child_mark_schema_as_dirty()
                # Invalidate our schema (the parent)
                self.mark_schema_as_dirty()

            self.child_collection.mark_schema_as_dirty = patched_mark_schema_as_dirty

    def mark_schema_as_dirty(self):
        self._last_schema = None

    @property
    def datasource(self) -> Datasource:
        return self._datasource

    @property
    def name(self) -> str:
        return self.child_collection.name

    @property
    def schema(self) -> CollectionSchema:
        # If the schema is not cached (at the first call, or after a markSchemaAsDirty call)
        if self._last_schema is None:
            self._last_schema = self._refine_schema(self.child_collection.schema)
        return self._last_schema

    def get_native_driver(self):
        return self.child_collection.get_native_driver()

    def get_field(self, name: str):
        try:
            return self.schema["fields"][name]
        except KeyError:
            raise CollectionException(f"No such field {name} in the collection {self.name}")

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        return sub_schema

    async def _refine_filter(
        self, caller: User, _filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        return _filter

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        refined_filter = cast(PaginatedFilter, await self._refine_filter(caller, _filter))
        return await self.child_collection.list(caller, refined_filter, projection)

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await self.child_collection.create(caller, data)

    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        refined_filter = cast(Optional[Filter], await self._refine_filter(caller, _filter))
        return await self.child_collection.update(caller, refined_filter, patch)

    async def delete(self, caller: User, _filter: Optional[Filter]) -> None:
        refined_filter = cast(Optional[Filter], await self._refine_filter(caller, _filter))
        return await self.child_collection.delete(caller, refined_filter)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        refined_filter = cast(Optional[Filter], await self._refine_filter(caller, _filter))
        return await self.child_collection.aggregate(caller, refined_filter, aggregation, limit)

    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        _filter: Optional[Filter] = None,
    ) -> ActionResult:
        refined_filter = cast(Filter, await self._refine_filter(caller, _filter))
        return await self.child_collection.execute(caller, name, data, refined_filter)

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        _filter: Optional[Filter] = None,
        meta: Optional[Dict[str, Any]] = dict(),
    ) -> List[ActionField]:
        refined_filter = cast(Optional[Filter], await self._refine_filter(caller, _filter))
        return await self.child_collection.get_form(caller, name, data, refined_filter, meta)

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        return await self.child_collection.render_chart(caller, name, record_id)
