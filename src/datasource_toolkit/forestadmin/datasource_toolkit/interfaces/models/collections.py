import abc
from typing import Callable, Dict, Generic, List, TypedDict, TypeVar

from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import Self


class CollectionSchema(TypedDict):
    actions: Dict[str, Action]
    fields: Dict[str, FieldAlias]
    searchable: bool
    segments: List[str]
    countable: bool
    charts: Dict[str, Callable]


class DatasourceSchema(TypedDict):
    charts: Dict[str, Callable]


class Collection(abc.ABC):
    @property
    @abc.abstractmethod
    def datasource(self) -> "Datasource[Self]":
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def schema(self) -> CollectionSchema:
        raise NotImplementedError


CovBoundCollection = TypeVar("CovBoundCollection", bound=Collection, covariant=True)
BoundCollection = TypeVar("BoundCollection", bound=Collection)


class Datasource(Generic[BoundCollection], abc.ABC):
    @property
    @abc.abstractmethod
    def collections(self) -> List[BoundCollection]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_collection(self, name: str) -> BoundCollection:
        raise NotImplementedError

    @abc.abstractmethod
    def get_native_query_connections(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def add_collection(self, collection: BoundCollection) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def schema(self) -> DatasourceSchema:
        raise NotImplementedError

    @abc.abstractmethod
    async def execute_native_query(
        self, connection_name: str, native_query: str, parameters: Dict[str, str]
    ) -> List[RecordsDataAlias]:
        raise NotImplementedError
