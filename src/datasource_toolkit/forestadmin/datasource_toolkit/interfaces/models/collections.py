import abc
from typing import Any, Callable, Dict, Generic, List, Optional, TypedDict, TypeVar, Union

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
    native_query_connections: List[str]


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
    def add_collection(self, collection: BoundCollection) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def schema(self) -> DatasourceSchema:
        raise NotImplementedError

    @abc.abstractmethod
    async def execute_native_query(self, connection_name: str, native_query: str) -> List[RecordsDataAlias]:
        raise NotImplementedError
