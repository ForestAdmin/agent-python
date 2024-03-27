from typing import Dict, Union
from urllib.parse import quote

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.chart_collection_decorator import ChartCollectionDecorator
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.chart.types import DataSourceChartDefinition
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


class ChartDataSourceDecorator(DatasourceDecorator):
    def __init__(self, child_datasource: Union[Datasource, "DatasourceDecorator"]) -> None:
        super().__init__(child_datasource, ChartCollectionDecorator)
        self.charts: Dict[str, DataSourceChartDefinition] = dict()

    def add_chart(self, name: str, chart_definition: DataSourceChartDefinition):
        if name in self.schema["charts"]:
            raise DatasourceToolkitException(f"Chart {name} already exists.")
        self.charts[name] = chart_definition
        chart_url = quote(f"/forest/_charts/{name}")
        ForestLogger.log("info", f"Chart {name} added with url: '{chart_url}'")

    async def render_chart(self, caller: User, name: str) -> Chart:
        chart_definition = self.charts.get(name)

        if chart_definition is not None:
            return await call_user_function(chart_definition, AgentCustomizationContext(self, caller), ResultBuilder)

        return await super().render_chart(caller, name)

    @property
    def schema(self):
        my_charts = self.charts
        other_charts = self.child_datasource.schema["charts"]
        for chart_name in my_charts.keys():
            if chart_name in other_charts.keys():
                raise DatasourceToolkitException(f"Chart {chart_name} is defined twice.")

        return {**self.child_datasource.schema, "charts": {**my_charts, **other_charts}}
