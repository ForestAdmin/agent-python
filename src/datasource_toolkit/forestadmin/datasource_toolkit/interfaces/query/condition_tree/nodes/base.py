import abc
import sys

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Awaitable, Callable, List, TypeVar, Union

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class ConditionTreeException(DatasourceToolkitException):
    pass


class ConditionTree(abc.ABC):
    @property
    @abc.abstractmethod
    def projection(self) -> Projection:
        pass

    @abc.abstractmethod
    def inverse(self) -> "ConditionTree":
        pass

    @abc.abstractmethod
    def match(self, record: RecordsDataAlias, collection: Collection, timezone: zoneinfo.ZoneInfo) -> bool:
        pass

    @abc.abstractmethod
    def replace(self, handler: "ReplacerAlias") -> "ConditionTree":
        pass

    @abc.abstractmethod
    async def replace_async(self, handler: "AsyncReplacerAlias") -> "ConditionTree":
        pass

    @abc.abstractmethod
    def apply(self, handler: "CallbackAlias") -> None:
        pass

    def filter(
        self, records: List[RecordsDataAlias], collection: Collection, timezone: zoneinfo.ZoneInfo
    ) -> List[RecordsDataAlias]:
        return list(filter(lambda record: self.match(record, collection, timezone), records))

    @abc.abstractmethod
    def unnest(self) -> "ConditionTree":
        pass

    @abc.abstractmethod
    def nest(self, prefix: str) -> "ConditionTree":
        pass


class ConditionTreeComponent(TypedDict):
    pass


HandlerResult = TypeVar("HandlerResult")
HandlerAlias = Callable[[ConditionTree], HandlerResult]
ReplacerAlias = HandlerAlias[Union[ConditionTree, ConditionTreeComponent]]
AsyncReplacerAlias = HandlerAlias[Awaitable[Union[ConditionTree, ConditionTreeComponent]]]
CallbackAlias = HandlerAlias[None]
