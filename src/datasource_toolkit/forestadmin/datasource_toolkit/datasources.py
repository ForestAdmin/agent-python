from typing import Any, Dict, List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource as DatasourceInterface
from forestadmin.datasource_toolkit.interfaces.models.collections import DatasourceSchema


class DatasourceException(DatasourceToolkitException):
    pass


class Datasource(DatasourceInterface[BoundCollection]):
    def __init__(self, live_query_connections: Optional[List[str]] = None) -> None:
        self._collections: Dict[str, BoundCollection] = {}
        self._live_query_connections = live_query_connections
        self._schema: DatasourceSchema = {
            "charts": {},
        }

    def get_native_query_connections(self) -> List[str]:
        return self._live_query_connections or []

    @property
    def schema(self) -> DatasourceSchema:
        return self._schema

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

    async def execute_native_query(self, connection_name: str, native_query: str, parameters: Dict[str, str]) -> Any:
        # in native_query, there is the following syntax:
        # - parameters to inject by 'execute' method are in the format '%(var)s'
        # - '%' (in 'like' comparisons) are replaced by '\%' (to avoid conflict with previous rule)
        raise NotImplementedError(f"'execute_native_query' is not implemented on {self.__class__.__name__}")
