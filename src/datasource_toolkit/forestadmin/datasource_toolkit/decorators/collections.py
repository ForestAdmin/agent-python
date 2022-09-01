import abc
from typing import List, Optional, Union, cast

from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import Self


class CollectionDecorator(Collection, abc.ABC):
    def __init__(self, collection: "CollectionDecorator", datasource: Datasource["CollectionDecorator"]):
        super().__init__()
        self.child_collection = collection
        self._datasource = datasource
        self._last_schema: Optional[CollectionSchema] = None
        self._last_child_schema: Optional[CollectionSchema] = None

    @property
    def name(self) -> str:
        return self.child_collection.name

    @property
    def datasource(self) -> Datasource[Self]:
        return self._datasource

    @property
    def schema(self) -> CollectionSchema:
        child_schema = self.child_collection.schema
        if not self._last_schema or self._last_child_schema != child_schema:
            self._last_schema = self._refine_schema(child_schema)
            self._last_child_schema = child_schema
        return child_schema

    async def execute(self, name: str, data: RecordsDataAlias, filter: Optional[Filter]) -> ActionResult:
        refined_filter = await self.refine_filter(filter)
        if refined_filter:
            refined_filter = cast(Filter, refined_filter)
        return await self.child_collection.execute(name, data, refined_filter)

    async def get_form(self, name: str, data: Optional[RecordsDataAlias], filter: Optional[Filter]) -> ActionField:
        refined_filter = await self.refine_filter(filter)
        if refined_filter:
            refined_filter = cast(Filter, refined_filter)
        return await self.child_collection.get_form(name, data, refined_filter)

    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await self.child_collection.create(data)

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        refined_filter = cast(PaginatedFilter, await self.refine_filter(filter))
        return await self.child_collection.list(refined_filter, projection)

    async def update(self, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        refined_filter = cast(Filter, await self.refine_filter(filter))
        return await self.child_collection.update(refined_filter, patch)

    async def delete(self, filter: Optional[Filter]) -> None:
        refined_filter = cast(Filter, await self.refine_filter(filter))
        await self.child_collection.delete(refined_filter)

    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        refined_filter = cast(Filter, await self.refine_filter(filter))
        return await self.child_collection.aggregate(refined_filter, aggregation, limit)

    def mark_schema_as_dirty(self) -> None:
        self._last_schema = None

    async def refine_filter(
        self, filter: Optional[Union[PaginatedFilter, Filter]]
    ) -> Optional[Union[PaginatedFilter, Filter]]:
        return filter

    @abc.abstractmethod
    def _refine_schema(self, child_schema: CollectionSchema) -> CollectionSchema:
        pass
