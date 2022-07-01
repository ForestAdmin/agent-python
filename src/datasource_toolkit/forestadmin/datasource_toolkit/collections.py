from typing import Dict, List

from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.actions import Action
from forestadmin.datasource_toolkit.interfaces.collections import Collection as CollectionInterface
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from typing_extensions import Self


class CollectionException(DatasourceException):
    pass


class Collection(CollectionInterface):
    def __init__(self, name: str, datasource: Datasource[Self]):
        super().__init__()
        self._datasource = datasource
        self._name = name
        self._schema: CollectionSchema = {
            "actions": {},
            "fields": {},
            "searchable": False,
            "segments": [],
        }

    def __repr__(self) -> str:
        return f"{self.name}: {self.schema}"

    @property
    def datasource(self) -> "Datasource[Self]":
        return self._datasource

    @property
    def name(self) -> str:
        return self._name

    @property
    def schema(self) -> CollectionSchema:
        return self._schema

    def add_action(self, name: str, action: Action):
        if name in self.schema["actions"]:
            raise CollectionException(f'Action "{name}" already defined in collection')
        self.schema["actions"][name] = action

    def add_field(self, name: str, field: FieldAlias):
        if name in self.schema["fields"]:
            raise CollectionException(f'Field "{name}" already defined in collection')
        self.schema["fields"][name] = field

    def get_field(self, name: str):
        try:
            return self.schema["fields"][name]
        except KeyError:
            raise CollectionException(f"No such field {name} in the collection {self.name}")

    def add_fields(self, fields: Dict[str, FieldAlias]):
        for name, field in fields.items():
            self.add_field(name, field)

    def add_segments(self, segments: List[str]):
        self.schema["segments"].extend(segments)

    def enable_search(self):
        self.schema["searchable"] = False
