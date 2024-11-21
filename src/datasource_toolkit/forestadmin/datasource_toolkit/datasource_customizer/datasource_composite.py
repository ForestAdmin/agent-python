from typing import Any, List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, DatasourceSchema


class CompositeDatasource(Datasource):
    def __init__(self) -> None:
        super().__init__()
        self._datasources: List[Datasource] = []

    @property
    def schema(self) -> DatasourceSchema:
        charts = {}
        native_queries = []
        for datasource in self._datasources:
            charts.update(datasource.schema["charts"])
            native_queries.extend(datasource.schema["native_query_connections"])

        return {"charts": charts, "native_query_connections": native_queries}

    @property
    def collections(self) -> List[BoundCollection]:
        ret = []
        for datasource in self._datasources:
            ret.extend(datasource.collections)
        return ret

    def get_collection(self, name: str) -> Any:
        for datasource in self._datasources:
            try:
                return datasource.get_collection(name)
            except Exception:
                pass

        collection_names = [c.name for c in self.collections]
        collection_names.sort()
        raise DatasourceToolkitException(
            f"Collection {name} not found. List of available collection: {', '.join(collection_names)}"
        )

    def add_datasource(self, datasource: Datasource):
        existing_collection_names = [c.name for c in self.collections]
        for collection in datasource.collections:
            if collection.name in existing_collection_names:
                raise DatasourceToolkitException(f"Collection '{collection.name}' already exists.")

        for connection in datasource.schema["charts"].keys():
            if connection in self.schema["charts"].keys():
                raise DatasourceToolkitException(f"Chart '{connection}' already exists.")

        for connection in datasource.schema["native_query_connections"]:
            if connection in self.schema["native_query_connections"]:
                raise DatasourceToolkitException(f"Native query connection '{connection}' already exists.")

        self._datasources.append(datasource)

    async def render_chart(self, caller: User, name: str) -> Chart:
        for datasource in self._datasources:
            if name in datasource.schema["charts"]:
                return await datasource.render_chart(caller, name)

        raise DatasourceToolkitException(f"Chart {name} is not defined in the datasource.")

    async def execute_native_query(self, connection_name: str, native_query: str) -> Any:
        for datasource in self._datasources:
            if connection_name in datasource.schema["native_query_connections"]:
                return await datasource.execute_native_query(connection_name, native_query)

        raise DatasourceToolkitException(
            f"Cannot find {connection_name} in datasources. "
            f"Existing connection names are: {','.join(self.schema['native_query_connections'])}"
        )
