from typing import Any, Dict, List
from urllib.parse import quote

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import CollectionException
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.chart.types import CollectionChartDefinition
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


class ChartCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        self._charts: Dict[str, CollectionChartDefinition] = dict()
        super().__init__(*args, **kwargs)

    def add_chart(self, name: str, definition: CollectionChartDefinition):
        if name in self.schema["charts"].keys():
            raise CollectionException(f"Chart {name} already exists.")

        self._charts[name] = definition
        chart_url = quote(f"/forest/_charts/{self.name}/{name}")
        ForestLogger.log("info", f"Chart {self.name}.{name} added with url: '{chart_url}'")
        self.mark_schema_as_dirty()

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        if self._charts.get(name) is not None:
            context = CollectionChartContext(caller, self, record_id)
            result_builder = ResultBuilder()
            ret = await call_user_function(self._charts[name], context, result_builder, record_id)
            return ret

        return await self.child_collection.render_chart(caller, name, record_id)

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        charts = {}
        for name, chart in self._charts.items():
            charts[name] = chart

        return {**sub_schema, "charts": charts}
