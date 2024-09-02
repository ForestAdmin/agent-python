from typing import List, Optional

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import connection, connections
from django.db.models import Model
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_django.interface import BaseDjangoCollection
from forestadmin.datasource_django.utils.model_introspection import DjangoCollectionFactory
from forestadmin.datasource_django.utils.native_driver_wrapper import NativeDriverWrapper, get_db_for_native_driver
from forestadmin.datasource_django.utils.polymorphic_util import DjangoPolymorphismUtil
from forestadmin.datasource_django.utils.query_factory import DjangoQueryBuilder
from forestadmin.datasource_django.utils.record_serializer import instance_to_record_data
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import is_column
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class DjangoCollection(BaseDjangoCollection):
    def __init__(self, datasource: Datasource, model: Model, support_polymorphic_relations: bool):
        super().__init__(model._meta.db_table, datasource)
        self._model = model
        self.support_polymorphic_relations = support_polymorphic_relations
        schema = DjangoCollectionFactory.build(model, support_polymorphic_relations)
        self.add_fields(schema["fields"])
        self.enable_count()

    @property
    def model(self) -> Model:
        return self._model

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        def _list():
            if self.support_polymorphic_relations:
                DjangoPolymorphismUtil.request_content_type()
            ret = [
                instance_to_record_data(item, projection, self)
                for item in DjangoQueryBuilder.mk_list(self, filter_, projection)
            ]
            if getattr(settings, "DEBUG"):
                ForestLogger.log("debug", f"SQL queries for list({len(connection.queries)}):{str(connection.queries)}")
            return ret

        return await sync_to_async(_list)()

    async def aggregate(
        self, caller: User, filter_: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        def _aggregate():
            if self.support_polymorphic_relations:
                DjangoPolymorphismUtil.request_content_type()
            ret = DjangoQueryBuilder.mk_aggregate(self, filter_, aggregation, limit)
            if getattr(settings, "DEBUG"):
                ForestLogger.log(
                    "debug", f"SQL queries for aggregate({len(connection.queries)}):{str(connection.queries)}"
                )
            return ret

        return await sync_to_async(_aggregate)()

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        projection = Projection(*[k for k in self.schema["fields"].keys() if is_column(self.schema["fields"][k])])

        def _create():
            if self.support_polymorphic_relations:
                DjangoPolymorphismUtil.request_content_type()
            ret = [instance_to_record_data(item, projection, self) for item in DjangoQueryBuilder.mk_create(self, data)]

            if getattr(settings, "DEBUG"):
                ForestLogger.log(
                    "debug", f"SQL queries for create({len(connection.queries)}):{str(connection.queries)}"
                )
            return ret

        return await sync_to_async(_create)()

    async def update(self, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias) -> None:
        def _update():
            if self.support_polymorphic_relations:
                DjangoPolymorphismUtil.request_content_type()
            DjangoQueryBuilder.mk_update(self, filter_, patch)
            if getattr(settings, "DEBUG"):
                ForestLogger.log(
                    "debug", f"SQL queries for update({len(connection.queries)}):{str(connection.queries)}"
                )

        await sync_to_async(_update)()

    async def delete(self, caller: User, filter_: Optional[Filter]) -> None:
        def _delete():
            if self.support_polymorphic_relations:
                DjangoPolymorphismUtil.request_content_type()
            DjangoQueryBuilder.mk_delete(self, filter_)
            if getattr(settings, "DEBUG"):
                ForestLogger.log(
                    "debug", f"SQL queries for delete({len(connection.queries)}):{str(connection.queries)}"
                )

        await sync_to_async(_delete)()

    def get_native_driver(self) -> NativeDriverWrapper:
        db_name = get_db_for_native_driver(self.model)
        return NativeDriverWrapper(connections[db_name])
