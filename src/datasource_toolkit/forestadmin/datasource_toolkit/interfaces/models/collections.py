import abc
from typing import Any, Callable, Dict, Generic, List, TypedDict, TypeVar

from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias
from typing_extensions import Self


class CollectionSchema(TypedDict):
    actions: Dict[str, Action]
    fields: Dict[str, FieldAlias]
    segments: List[str]
    charts: Dict[str, Callable]

    # collection capabilities
    # it should be in the form of 'canSomething' but countable & searchable already exists
    # because I'm lazy, I'm so sorry for 'chartable' 😅
    listable: bool
    creatable: bool
    updatable: bool
    deletable: bool
    chartable: bool
    countable: bool
    searchable: bool
    support_native_query: bool


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
    @classmethod
    @abc.abstractmethod
    def mk_meta_entry(cls) -> Dict[str, Any]:
        raise NotImplementedError

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
