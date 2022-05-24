import abc
from typing import Dict, Generic, List, TypeVar

from typing_extensions import Self, TypedDict

from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias


class CollectionSchema(TypedDict):
    actions: Dict[str, Action]
    fields: Dict[str, FieldAlias]
    searchable: bool
    segments: List[str]


class Collection(abc.ABC):
    @abc.abstractproperty
    def datasource(self) -> "Datasource[Self]":
        raise NotImplementedError

    @abc.abstractproperty
    def name(self) -> str:
        raise NotImplementedError

    @abc.abstractproperty
    def schema(self) -> CollectionSchema:
        raise NotImplementedError


CovBoundCollection = TypeVar("CovBoundCollection", bound=Collection, covariant=True)
BoundCollection = TypeVar("BoundCollection", bound=Collection)


class Datasource(Generic[BoundCollection], abc.ABC):
    @abc.abstractproperty
    def collections(self) -> List[BoundCollection]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_collection(self, name: str) -> BoundCollection:
        raise NotImplementedError

    @abc.abstractmethod
    def add_collection(self, collection: BoundCollection) -> None:
        raise NotImplementedError
