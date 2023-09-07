import sys
from typing import Any, Generic, Optional, TypedDict, TypeVar, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
    ConditionTreeComponent,
)
from typing_extensions import Self, TypeGuard


class FilterComponent(TypedDict, total=False):
    condition_tree: ConditionTree
    search: Optional[str]
    search_extended: bool
    segment: Optional[str]
    timezone: zoneinfo.ZoneInfo


class PlainFilter(TypedDict, total=False):
    condition_tree: ConditionTreeComponent
    search: Optional[str]
    search_extended: bool
    segment: Optional[str]
    timezone: str


T = TypeVar("T", bound=FilterComponent)


class FilterException(DatasourceToolkitException):
    pass


class BaseFilter(Generic[T]):
    def __init__(self, filter: T):
        self.condition_tree = filter.get("condition_tree")
        self.search = filter.get("search")
        self.search_extended = filter.get("search_extended")
        self.segment = filter.get("segment")
        self.timezone = filter.get("timezone")

    def __eq__(self, obj: Self):
        res = False
        if self.__class__ == obj.__class__:
            res = (
                self.condition_tree == obj.condition_tree
                and self.search == obj.search
                and self.search_extended == obj.search_extended
                and self.segment == obj.segment
                and self.timezone == obj.timezone
            )

        return res

    @property
    def is_nestable(self) -> bool:
        return not self.search and not self.segment

    def to_filter_component(self) -> T:
        kw = {}
        if self.condition_tree:
            kw["condition_tree"] = self.condition_tree
        if self.search:
            kw["search"] = self.search
        if self.search_extended:
            kw["search_extended"] = self.search_extended
        if self.segment:
            kw["segment"] = self.segment
        if self.timezone:
            kw["timezone"] = self.timezone
        return cast(T, kw)

    def override_component(self, filter: T) -> T:
        component = self.to_filter_component()
        component.update(filter)
        return component

    def override(self, filter: T) -> Self:
        return self.__class__(self.override_component(filter))

    def _nest_arguments(self, prefix: str) -> T:
        if not self.condition_tree:
            return cast(T, {})
        return cast(T, {"condition_tree": self.condition_tree.nest(prefix)})

    def nest(self, prefix: str) -> Self:
        if not self.is_nestable:
            raise DatasourceToolkitException("Filter can't be nested")
        try:
            return self.override(self._nest_arguments(prefix))
        except DatasourceToolkitException:
            return self


class Filter(BaseFilter[FilterComponent]):
    pass


def is_filter(filter: Any) -> TypeGuard[Filter]:
    return isinstance(filter, Filter)
