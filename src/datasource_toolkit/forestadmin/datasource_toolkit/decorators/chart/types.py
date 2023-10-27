from typing import Callable

from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.interfaces.chart import Chart

DataSourceChartDefinition = Callable[[AgentCustomizationContext, ResultBuilder], Chart]
CollectionChartDefinition = Callable[[CollectionChartContext, ResultBuilder], Chart]
