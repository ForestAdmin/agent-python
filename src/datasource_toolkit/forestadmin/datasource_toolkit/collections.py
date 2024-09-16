from typing import Any, Dict, List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.actions import ActionFormElement, ActionResult
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.collections import Collection as CollectionInterface
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import Self

# from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict


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
            "countable": False,
            "charts": {},
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

    def add_action(self, name: str, action: "ActionDict"):  # noqa:F821
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
        self.schema["searchable"] = True

    def enable_count(self):
        self.schema["countable"] = True

    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        filter_: Optional[Filter],
    ) -> ActionResult:
        """to execute an action"""
        raise ForestException(f"Action {name} is not implemented")

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias] = None,
        filter_: Optional[Filter] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[ActionFormElement]:
        """to get the form of an action"""
        return []

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        """to render a chart"""
        raise ForestException(f"Chart {name} is not implemented")
