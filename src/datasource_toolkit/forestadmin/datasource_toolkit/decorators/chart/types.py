from typing import Awaitable, Callable, Union

from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias

DataSourceChartDefinition = Callable[[AgentCustomizationContext, ResultBuilder], Union[Chart, Awaitable[Chart]]]
CollectionChartDefinition = Callable[
    [CollectionChartContext, ResultBuilder, CompositeIdAlias], Union[Chart, Awaitable[Chart]]
]
