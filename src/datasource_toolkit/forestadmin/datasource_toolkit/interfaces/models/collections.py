import abc
import copy
from typing import Dict, Generic, List, TypeVar

from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias
from typing_extensions import Self, TypedDict


class JsonCollectionSchema:
    @staticmethod
    def dumps(schema: "CollectionSchema"):
        jsoned = copy.deepcopy(schema)
        for name, field in schema["fields"].items():
            jsoned["fields"][name] = {**field, "type": field["type"].value}
            if jsoned["fields"][name].get("column_type"):
                jsoned["fields"][name]["column_type"] = jsoned["fields"][name]["column_type"].value
            if jsoned["fields"][name].get("filter_operators"):
                jsoned["fields"][name]["filter_operators"] = [
                    op.value for op in jsoned["fields"][name]["filter_operators"]
                ]

            if jsoned["fields"][name].get("validations"):
                jsoned["fields"][name]["validations"] = [
                    {"operator": v["operator"].value, "value": v.get("value")}
                    for v in jsoned["fields"][name]["validations"]
                ]
        return jsoned


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
