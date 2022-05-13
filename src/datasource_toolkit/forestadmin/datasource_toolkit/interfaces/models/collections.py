import abc
from typing import Dict, List

from typing_extensions import TypedDict

from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias


class CollectionSchema(TypedDict):
    actions: Dict[str, Action]
    fields: Dict[str, FieldAlias]
    searchable: bool
    segments: List[str]


class Collection(abc.ABC):
    @abc.abstractproperty
    def datasource(self) -> "Datasource":
        raise NotImplementedError

    @abc.abstractproperty
    def name(self) -> str:
        raise NotImplementedError

    @abc.abstractproperty
    def schema(self) -> CollectionSchema:
        raise NotImplementedError


class Datasource(abc.ABC):
    @abc.abstractproperty
    def collections(self) -> Dict[str, Collection]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_collection(self, name: str) -> Collection:
        raise NotImplementedError

    @abc.abstractmethod
    def add_collection(self, collection: Collection) -> None:
        raise NotImplementedError
