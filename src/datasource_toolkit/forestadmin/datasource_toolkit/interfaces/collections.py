import abc
from typing import List, Optional

from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection as CollectionModel
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class Collection(CollectionModel, abc.ABC):
    @abc.abstractmethod
    async def execute(
        self,
        name: str,
        data: RecordsDataAlias,
        filter: Optional[Filter],
    ) -> ActionResult:
        pass

    @abc.abstractmethod
    async def get_form(
        self,
        name: str,
        data: Optional[RecordsDataAlias],
        filter: Optional[Filter],
    ) -> List[ActionField]:
        pass

    @abc.abstractmethod
    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        pass

    @abc.abstractmethod
    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        pass

    @abc.abstractmethod
    async def update(self, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        pass

    @abc.abstractmethod
    async def delete(self, filter: Optional[Filter]) -> None:
        pass

    @abc.abstractmethod
    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        pass
