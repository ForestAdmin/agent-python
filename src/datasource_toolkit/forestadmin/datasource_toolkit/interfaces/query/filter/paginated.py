from typing import Any, Dict, List, Optional, cast

from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import (
    BaseFilter,
    Filter,
    FilterComponent,
    PlainFilter,
)
from forestadmin.datasource_toolkit.interfaces.query.page import Page, PlainPage
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause, Sort
from typing_extensions import Self, TypeGuard


class PaginatedFilterComponent(FilterComponent, total=False):
    page: Page
    sort: Sort


class PlainPaginatedFilter(PlainFilter):
    sort: Optional[List[PlainSortClause]]
    page: Optional[PlainPage]


class PaginatedFilter(BaseFilter[PaginatedFilterComponent]):
    def __init__(self, filter: PaginatedFilterComponent):
        super().__init__(filter)
        self.sort: Sort = filter.get("sort")
        self.page: Page = filter.get("page")

    def __eq__(self, object: Self):
        return super(PaginatedFilter, self).__eq__(object) and self.sort == object.sort and self.page == object.page

    @staticmethod
    def from_base_filter(filter: Optional[Filter]) -> "PaginatedFilter":
        kwargs: Dict[str, Any] = {"sort": None, "page": None}
        if filter is None:
            return PaginatedFilter(PaginatedFilterComponent(**kwargs))

        if filter.condition_tree:
            kwargs["condition_tree"] = filter.condition_tree
        if filter.search:
            kwargs["search"] = filter.search
        if filter.search_extended:
            kwargs["search_extended"] = filter.search_extended
        if filter.segment:
            kwargs["segment"] = filter.segment
        if filter.timezone:
            kwargs["timezone"] = filter.timezone
        return PaginatedFilter(PaginatedFilterComponent(**kwargs))

    def to_base_filter(self) -> Filter:
        kwargs = {}
        if self.condition_tree:
            kwargs["condition_tree"] = self.condition_tree
        if self.search:
            kwargs["search"] = self.search
        if self.search_extended:
            kwargs["search_extended"] = self.search_extended
        if self.segment:
            kwargs["segment"] = self.segment
        if self.timezone:
            kwargs["timezone"] = self.timezone
        return Filter(FilterComponent(**kwargs))

    def to_filter_component(self) -> PaginatedFilterComponent:
        paginated_filter_component = {**super().to_filter_component()}
        if self.sort:
            paginated_filter_component["sort"] = self.sort
        if self.page:
            paginated_filter_component["page"] = self.page
        return cast(PaginatedFilterComponent, paginated_filter_component)

    def _nest_arguments(self, prefix: str) -> PaginatedFilterComponent:
        args = {**super()._nest_arguments(prefix)}
        if self.sort:
            args["sort"] = self.sort.nest(prefix)
        return cast(PaginatedFilterComponent, args)


def is_paginated_filter(filter: Any) -> TypeGuard[PaginatedFilter]:
    return isinstance(filter, PaginatedFilter)
