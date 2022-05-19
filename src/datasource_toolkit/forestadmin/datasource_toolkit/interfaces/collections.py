import abc
from typing import List, Optional

from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    Collection as CollectionModel,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    AggregateResult,
    Aggregation,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import (
    PaginatedFilter,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class Collection(CollectionModel, abc.ABC):
    @abc.abstractmethod
    async def execute(
        self,
        name: str,
        data: RecordsDataAlias,
        filter: Optional[PaginatedFilter],
    ) -> ActionResult:
        pass

    @abc.abstractmethod
    async def get_form(
        self,
        name: str,
        data: Optional[RecordsDataAlias],
        filter: Optional[PaginatedFilter],
    ) -> ActionField:
        pass

    @abc.abstractmethod
    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        pass

    @abc.abstractmethod
    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        pass

    @abc.abstractmethod
    async def update(self, filter: PaginatedFilter, patch: RecordsDataAlias) -> None:
        pass

    @abc.abstractmethod
    async def delete(self, filter: PaginatedFilter) -> None:
        pass

    @abc.abstractmethod
    async def aggregate(
        self, filter: PaginatedFilter, aggregation: Aggregation, limit: Optional[int]
    ) -> List[AggregateResult]:
        pass
