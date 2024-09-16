import abc
from typing import Any, Dict, List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.interfaces.actions import ActionFormElement, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection as CollectionModel
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class Collection(CollectionModel, abc.ABC):
    @abc.abstractmethod
    def get_native_driver(self):
        """return native driver"""

    @abc.abstractmethod
    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        filter_: Optional[Filter],
    ) -> ActionResult:
        """to execute an action"""

    @abc.abstractmethod
    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        filter_: Optional[Filter],
        meta: Optional[Dict[str, Any]],
    ) -> List[ActionFormElement]:
        """to get the form of an action"""

    @abc.abstractmethod
    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        """to render a chart"""

    @abc.abstractmethod
    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        """to create records"""

    @abc.abstractmethod
    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        """to list records"""

    @abc.abstractmethod
    async def update(self, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias) -> None:
        """to update records"""

    @abc.abstractmethod
    async def delete(self, caller: User, filter_: Optional[Filter]) -> None:
        """to delete records"""

    @abc.abstractmethod
    async def aggregate(
        self, caller: User, filter_: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        """to make aggregate request"""
