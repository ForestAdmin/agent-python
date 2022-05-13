from typing import cast

from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import (
    BaseFilter,
    FilterComponent,
)
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort


class PaginatedFilterComponent(FilterComponent, total=False):
    page: Page
    sort: Sort


class PaginatedFilter(BaseFilter[PaginatedFilterComponent]):
    def __init__(self, filter: PaginatedFilterComponent):
        super().__init__(filter)
        self.sort = filter.get("sort")
        self.page = filter.get("page")

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
            args["sort"] = self.sort
        return cast(PaginatedFilterComponent, args)
