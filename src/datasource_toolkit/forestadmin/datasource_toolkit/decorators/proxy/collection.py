from typing import List, Optional, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class ProxyMixin:
    def __init__(self, collection: Collection, datasource: Datasource[BoundCollection]):
        self.child_collection = collection
        self.child_collection._datasource = datasource  # type: ignore
        self.child_collection._schema = self.schema  # type: ignore

    def __getattr__(self, name: str):
        return getattr(self.child_collection, name)

    @property
    def schema(self) -> CollectionSchema:
        return self.child_collection.schema

    async def _refine_filter(
        self, filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        return filter

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        try:
            refined_filter = cast(PaginatedFilter, await self._refine_filter(filter))
        except Exception:
            return []
        else:
            return await self.child_collection.list(refined_filter, projection)  # type: ignore

    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await self.child_collection.create(data)

    async def execute(
        self,
        name: str,
        data: RecordsDataAlias,
        filter: Optional[Filter],
    ) -> ActionResult:
        refined_filter = cast(Filter, await self._refine_filter(filter))
        return await self.child_collection.execute(name, data, refined_filter)

    async def get_form(
        self,
        name: str,
        data: Optional[RecordsDataAlias],
        filter: Optional[Filter],
    ) -> List[ActionField]:
        refined_filter = cast(Optional[Filter], await self._refine_filter(filter))
        return await self.child_collection.get_form(name, data, refined_filter)

    async def update(self, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        refined_filter = cast(Optional[Filter], await self._refine_filter(filter))
        return await self.child_collection.update(refined_filter, patch)

    async def delete(self, filter: Optional[Filter]) -> None:
        refined_filter = cast(Optional[Filter], await self._refine_filter(filter))
        return await self.child_collection.delete(refined_filter)

    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        refined_filter = cast(Optional[Filter], await self._refine_filter(filter))
        return await self.child_collection.aggregate(refined_filter, aggregation, limit)
