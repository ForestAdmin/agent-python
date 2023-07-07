from typing import Awaitable, Dict, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.chart_collection_decorator import ChartCollectionDecorator
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.chart.types import DataSourceChartDefinition
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.chart import Chart


class ChartDataSourceDecorator(DatasourceDecorator):
    def __init__(self, child_datasource: Union[Datasource, "DatasourceDecorator"]) -> None:
        super().__init__(child_datasource, ChartCollectionDecorator)
        self.charts: Dict[str, DataSourceChartDefinition] = dict()

    def add_chart(self, name: str, chart_definition: DataSourceChartDefinition):
        if name in self.schema["charts"]:
            raise DatasourceToolkitException(f"Chart {name} already exists.")
        self.charts[name] = chart_definition

    async def render_chart(self, caller: User, name: str) -> Chart:
        chart_definition = self.charts.get(name)

        if chart_definition is not None:
            ret = chart_definition(AgentCustomizationContext(self, caller), ResultBuilder)
            if isinstance(ret, Awaitable):
                ret = await ret
            return ret

        return await super().render_chart(caller, name)

    @property
    def schema(self):
        my_charts = self.charts
        other_charts = self.child_datasource.schema["charts"]
        for chart_name in my_charts.keys():
            if chart_name in other_charts.keys():
                raise DatasourceToolkitException(f"Chart {chart_name} is defined twice.")

        return {**self.child_datasource.schema, "charts": {**my_charts, **other_charts}}
