from typing import Any, Awaitable, Dict, List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import CollectionException
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.chart.types import CollectionChartDefinition
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class ChartCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        self._charts: Dict[str, CollectionChartDefinition] = dict()
        super().__init__(*args, **kwargs)

    def add_chart(self, name: str, definition: CollectionChartDefinition):
        if name in self.schema["charts"].keys():
            raise CollectionException(f"Chart {name} already exists.")

        self._charts[name] = definition
        self.mark_schema_as_dirty()

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        if self._charts.get(name) is not None:
            context = CollectionChartContext(caller, self, record_id)
            result_builder = ResultBuilder()
            ret = self._charts[name](context, result_builder, record_id)
            if isinstance(ret, Awaitable):
                ret = await ret
            return ret

        return await self.child_collection.render_chart(caller, name, record_id)

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        charts = {}
        for name, chart in self._charts.items():
            charts[name] = chart

        return {**sub_schema, "charts": charts}
