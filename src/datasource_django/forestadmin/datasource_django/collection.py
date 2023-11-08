from typing import Any, Callable, Dict, List, Optional

from django.db.models import Model
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.model_converter import DjangoCollectionFactory
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoCollection(BaseDjangoCollection):
    def __init__(self, datasource: Datasource, model: Model):
        super().__init__(model.__name__, datasource)
        self._model = model
        schema = DjangoCollectionFactory.build(model)
        self.add_fields(schema["fields"])

    def get_column(self, name: str):
        return super().get_column(name)

    @property
    def model(self) -> Optional[Callable[[Any], Any]]:
        return self._model

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        return await super().list(caller, filter_, projection)

    async def aggregate(
        self, caller: User, filter_: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        return await super().aggregate(caller, filter_, aggregation, limit)

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await super().create(caller, data)

    async def update(self, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias) -> None:
        return await super().update(caller, filter_, patch)

    async def delete(self, caller: User, filter_: Optional[Filter]) -> None:
        return await super().delete(caller, filter_)

    async def execute(
        self, caller: User, name: str, data: RecordsDataAlias, filter_: Optional[Filter]
    ) -> ActionResult:  # duplicate
        return await super().execute(caller, name, data, filter_)

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        filter_: Optional[Filter],
        meta: Optional[Dict[str, Any]],
    ) -> List[ActionField]:  # duplicate
        return await super().get_form(caller, name, data, filter_, meta)

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:  # duplicate
        return await super().render_chart(caller, name, record_id)

    def get_native_driver(self):
        return super().get_native_driver()
