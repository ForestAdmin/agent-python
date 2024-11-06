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
        for datasource in self._datasources:
            charts.update(datasource.schema["charts"])
        return {"charts": charts}

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

        for chart_name in datasource.schema["charts"].keys():
            if chart_name in self.schema["charts"].keys():
                raise DatasourceToolkitException(f"Chart '{chart_name}' already exists.")

        self._datasources.append(datasource)

    async def render_chart(self, caller: User, name: str) -> Chart:
        for datasource in self._datasources:
            if name in datasource.schema["charts"]:
                return await datasource.render_chart(caller, name)

        raise DatasourceToolkitException(f"Chart {name} is not defined in the datasource.")
