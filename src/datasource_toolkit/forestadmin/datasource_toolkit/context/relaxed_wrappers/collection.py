from typing import List, Optional, Union, cast

from forestadmin.datasource_toolkit.datasources import DatasourceException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
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
        collection = super().get_collection(name)
        return RelaxedCollection(collection)

    def add_collection(self, collection: "RelaxedCollection") -> None:
        raise RelaxedDatasourceException("Cannot modify existing datasources")


class RelaxedCollection(Collection):
    def __init__(self, collection: Collection):
        self.collection = collection

    @property
    def datasource(self) -> Datasource[Self]:
        self.collection.datasource
        return RelaxedDatasource(self.collection.datasource)

    @property
    def name(self) -> str:
        return self.collection.name

    @property
    def schema(self):
        return self.collection.schema

    async def execute(
        self, name: str, data: RecordsDataAlias, filter: Optional[Union[Filter, PlainFilter]]
    ) -> ActionResult:
        filter_instance = self._build_filter(filter)
        return await self.collection.execute(name, data, filter_instance)

    async def get_form(
        self, name: str, data: Optional[RecordsDataAlias], filter: Optional[Filter]
    ) -> List[ActionField]:
        filter_instance = self._build_filter(filter)
        return await super().get_form(name, data, filter_instance)

    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        return await self.collection.create(data)

    def _build_filter(self, filter: Optional[Union[Filter, PlainFilter]]) -> Optional[Filter]:
        if not filter:
            return None
        elif is_filter(filter):
            return filter
        else:
            plain_filter = cast(PlainFilter, filter)
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

    def _build_paginated_filter(self, filter: Union[PaginatedFilter, PlainPaginatedFilter]):
        if is_paginated_filter(filter):
            return filter

        filter = cast(PlainPaginatedFilter, filter)
        filter_component: PaginatedFilterComponent = {
            "search": filter.get("search"),
            "search_extended": filter.get("search_extended", False),
            "segment": filter.get("segment"),
            "timezone": filter.get("timezone"),  # type: ignore
        }

        if filter.get("condition_tree"):
            filter_component["condition_tree"] = ConditionTreeFactory.from_plain_object(filter.get("condition_tree"))

        if filter.get("sort"):
            sort_clauses = cast(List[PlainSortClause], filter.get("sort"))
            filter_component["sort"] = Sort(sort_clauses)

        if filter.get("page"):
            plain_page = cast(PlainPage, filter.get("page"))
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
        self, filter: Union[PaginatedFilter, PlainPaginatedFilter], projection: Projection
    ) -> List[RecordsDataAlias]:
        filter_instance = self._build_paginated_filter(filter)
        projection_instance = self._build_projection(projection)

        return await self.collection.list(filter_instance, projection_instance)

    async def update(self, filter: Optional[Union[Filter, PlainFilter]], patch: RecordsDataAlias) -> None:
        filter_instance = self._build_filter(filter)
        return await self.collection.update(filter_instance, patch)

    async def delete(self, filter: Optional[Union[Filter, PlainFilter]]) -> None:
        filter_instance = self._build_filter(filter)
        return await self.collection.delete(filter_instance)

    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        filter_instance = self._build_filter(filter)
        aggregation_instance = self._build_aggregation(aggregation)

        return await self.collection.aggregate(filter_instance, aggregation_instance, limit)
