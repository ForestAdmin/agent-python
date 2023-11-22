from typing import Any, Dict, List, Optional

from django.db.models import Model
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.model_introspection import DjangoCollectionFactory
from forestadmin.datasource_django.utils.query_factory import DjangoQueryBuilder
from forestadmin.datasource_django.utils.record_serializer import instance_to_record_data
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import is_column
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

    @property
    def model(self) -> Model:
        return self._model

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        return [
            instance_to_record_data(item, projection)
            for item in await DjangoQueryBuilder.mk_list(self, filter_, projection)
        ]

    async def aggregate(
        self, caller: User, filter_: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        return await DjangoQueryBuilder.mk_aggregate(self, filter_, aggregation, limit)

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        instances = await DjangoQueryBuilder.mk_create(self, data)
        projection = Projection(*[k for k in self.schema["fields"].keys() if is_column(self.schema["fields"][k])])
        return [instance_to_record_data(item, projection) for item in instances]

    async def update(self, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias) -> None:
        await DjangoQueryBuilder.mk_update(self, filter_, patch)

    async def delete(self, caller: User, filter_: Optional[Filter]) -> None:
        await DjangoQueryBuilder.mk_delete(self, filter_)

    async def execute(
        self, caller: User, name: str, data: RecordsDataAlias, filter_: Optional[Filter]
    ) -> ActionResult:  # TODO: duplicate
        return await super().execute(caller, name, data, filter_)

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        filter_: Optional[Filter],
        meta: Optional[Dict[str, Any]],
    ) -> List[ActionField]:  # TODO: duplicate
        return await super().get_form(caller, name, data, filter_, meta)

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:  # duplicate
        return await super().render_chart(caller, name, record_id)

    def get_native_driver(self):
        # TODO
        return super().get_native_driver()