import abc
import sys
from typing import Any, Awaitable, Callable, Dict, List, TypeVar, Union

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import TypedDict


class ConditionTreeException(DatasourceToolkitException):
    pass


class ConditionTree(abc.ABC):
    @property
    @abc.abstractmethod
    def projection(self) -> Projection:
        """return all fields manipulated by conditionTree"""

    @abc.abstractmethod
    def inverse(self) -> "ConditionTree":
        """inverse conditionTree"""

    @abc.abstractmethod
    def match(self, record: RecordsDataAlias, collection: Collection, timezone: zoneinfo.ZoneInfo) -> bool:
        """return conditionTree matching record"""

    @abc.abstractmethod
    def some_leaf(self, handler: Callable[["ConditionTreeLeaf"], bool]) -> bool:  # noqa:F821 # type: ignore
        """return bool if handler return True for at least on leaf"""

    @abc.abstractmethod
    def replace(self, handler: "ReplacerAlias") -> "ConditionTree":
        """replace in conditionTree applying hander"""

    @abc.abstractmethod
    async def replace_async(self, handler: "AsyncReplacerAlias") -> "ConditionTree":
        """like replace but async handler"""

    @abc.abstractmethod
    def apply(self, handler: "CallbackAlias") -> None:
        """apply handler to condition tree"""

    def filter(
        self, records: List[RecordsDataAlias], collection: Collection, timezone: zoneinfo.ZoneInfo
    ) -> List[RecordsDataAlias]:
        return list(filter(lambda record: self.match(record, collection, timezone), records))

    @abc.abstractmethod
    def unnest(self) -> "ConditionTree":
        """un nest conditionTree"""

    @abc.abstractmethod
    def nest(self, prefix: str) -> "ConditionTree":
        """nest conditionTree"""

    @abc.abstractmethod
    def to_plain_object(self) -> Dict[str, Any]:
        """return a component version of self. Inverse of ConditionTreeFactory.from_plain_object"""

    @abc.abstractmethod
    def for_each_leaf(self, handler: Callable[["ConditionTreeLeaf"], None]):  # type:ignore # noqa: F821
        """call handler method for each leaf"""


class ConditionTreeComponent(TypedDict):
    pass


HandlerResult = TypeVar("HandlerResult")
HandlerAlias = Callable[[ConditionTree], HandlerResult]
ReplacerAlias = HandlerAlias[Union[ConditionTree, ConditionTreeComponent]]
AsyncReplacerAlias = HandlerAlias[Awaitable[Union[ConditionTree, ConditionTreeComponent]]]
CallbackAlias = HandlerAlias[None]
