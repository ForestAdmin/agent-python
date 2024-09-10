from typing import Any, Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.datasources import DatasourceException
from forestadmin.datasource_toolkit.interfaces.actions import ActionFormElement, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    AggregateResult,
    Aggregation,
    PlainAggregation,
    is_aggregation,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import (
    PaginatedFilter,
    PaginatedFilterComponent,
    PlainPaginatedFilter,
    is_paginated_filter,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import (
    Filter,
    FilterComponent,
    PlainFilter,
    is_filter,
)
from forestadmin.datasource_toolkit.interfaces.query.page import Page, PlainPage
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection, is_projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause, Sort
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import Self


class RelaxedDatasourceException(DatasourceException):
    pass


class RelaxedDatasource(Datasource["RelaxedCollection"]):
    def __init__(self, datasource: Datasource[Collection]):
        self.datasource = datasource

    @property
    def collections(self) -> List["RelaxedCollection"]:
        return [RelaxedCollection(collection) for collection in self.datasource.collections]

    def get_collection(self, name: str) -> "RelaxedCollection":
        collection = self.datasource.get_collection(name)
        return RelaxedCollection(collection)

    def add_collection(self, collection: "RelaxedCollection") -> None:
        raise RelaxedDatasourceException("Cannot modify existing datasources")


class RelaxedCollection(Collection):
    def __init__(self, collection: Collection):
        self.collection = collection

    def get_native_driver(self) -> Any:
        return self.collection.get_native_driver()

    @property
    def datasource(self) -> Datasource[Self]:
        self.collection.datasource
        return RelaxedDatasource(self.collection.datasource)  # type:ignore

    @property
    def name(self) -> str:
        return self.collection.name

    @property
    def schema(self):
        return self.collection.schema

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await self.collection.create(caller, data)

    def _build_filter(self, filter_: Optional[Union[Filter, PlainFilter]]) -> Optional[Filter]:
        if not filter_:
            return None
        elif is_filter(filter_):
            return filter_
        else:
            plain_filter = cast(PlainFilter, filter_)
            condition_tree = None
            if plain_filter.get("condition_tree"):
                condition_tree = ConditionTreeFactory.from_plain_object(plain_filter.get("condition_tree"))
            component = cast(
                FilterComponent,
                {
                    **plain_filter,
                    "condition_tree": condition_tree,
                },
            )
            return Filter(component)

    def _build_paginated_filter(self, filter_: Union[PaginatedFilter, PlainPaginatedFilter]):
        if is_paginated_filter(filter_):
            return filter_

        filter_ = cast(PlainPaginatedFilter, filter_)
        filter_component: PaginatedFilterComponent = {
            "search": filter_.get("search"),
            "search_extended": filter_.get("search_extended", False),
            "segment": filter_.get("segment"),
            "timezone": filter_.get("timezone"),  # type: ignore
        }

        if filter_.get("condition_tree"):
            filter_component["condition_tree"] = ConditionTreeFactory.from_plain_object(filter_.get("condition_tree"))

        if filter_.get("sort"):
            sort_clauses = cast(List[PlainSortClause], filter_.get("sort"))
            filter_component["sort"] = Sort(sort_clauses)

        if filter_.get("page"):
            plain_page = cast(PlainPage, filter_.get("page"))
            filter_component["page"] = Page(plain_page["skip"], plain_page["limit"])

        return PaginatedFilter(PaginatedFilterComponent(**filter_component))

    def _build_projection(self, projection: Union[Projection, List[str]]) -> Projection:
        if is_projection(projection):
            return projection
        return Projection(*projection)

    def _build_aggregation(self, aggregation: Union[Aggregation, PlainAggregation]) -> Aggregation:
        if is_aggregation(aggregation):
            return aggregation
        aggregation = cast(PlainAggregation, aggregation)
        return Aggregation(aggregation)

    async def list(
        self,
        caller: User,
        filter_: Union[PaginatedFilter, PlainPaginatedFilter],
        projection: Union[Projection, List[str]],
    ) -> List[RecordsDataAlias]:
        filter_instance = self._build_paginated_filter(filter_)
        projection_instance = self._build_projection(projection)

        return await self.collection.list(caller, filter_instance, projection_instance)

    async def update(
        self, caller: User, filter_: Optional[Union[Filter, PlainFilter]], patch: RecordsDataAlias
    ) -> None:
        filter_instance = self._build_filter(filter_)
        return await self.collection.update(caller, filter_instance, patch)

    async def delete(self, caller: User, filter_: Optional[Union[Filter, PlainFilter]]) -> None:
        filter_instance = self._build_filter(filter_)
        return await self.collection.delete(caller, filter_instance)

    async def aggregate(
        self, caller: User, filter_: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        filter_instance = self._build_filter(filter_)
        aggregation_instance = self._build_aggregation(aggregation)

        return await self.collection.aggregate(caller, filter_instance, aggregation_instance, limit)

    async def execute(
        self, caller: User, name: str, data: RecordsDataAlias, filter_: Optional[Union[Filter, PlainFilter]]
    ) -> ActionResult:
        filter_instance = self._build_filter(filter_)
        return await self.collection.execute(caller, name, data, filter_instance)

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        filter_: Optional[Filter],
        meta: Optional[Dict[str, Any]],
    ) -> List[ActionFormElement]:
        filter_instance = self._build_filter(filter_)
        return await super().get_form(caller, name, data, filter_instance, meta)

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        return await super().render_chart(caller, name, record_id)
