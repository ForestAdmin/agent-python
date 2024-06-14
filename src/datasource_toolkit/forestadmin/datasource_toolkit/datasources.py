from typing import Dict, List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource as DatasourceInterface


class DatasourceException(DatasourceToolkitException):
    pass


class Datasource(DatasourceInterface[BoundCollection]):
    def __init__(self) -> None:
        self._collections: Dict[str, BoundCollection] = {}

    @property
    def schema(self):
        return {"charts": {}}

    @property
    def collections(self) -> List[BoundCollection]:
        return list(self._collections.values())

    def get_collection(self, name: str) -> BoundCollection:
        collection_names = self._collections.keys()
        if name not in collection_names:
            raise DatasourceException(
                f"Collection '{name}' not found. Available collections are: {', '.join(collection_names)}"
            )

        collection: BoundCollection = self._collections[name]
        return collection

    def add_collection(self, collection: BoundCollection) -> None:
        if collection.name in self._collections:
            raise DatasourceException(f"Collection '{collection.name}' already defined in datasource")
        self._collections[collection.name] = collection

    async def render_chart(self, caller: User, name: str) -> Chart:
        raise DatasourceException(f"Chart {name} not exists on this datasource.")
