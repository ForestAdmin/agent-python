from typing import Optional, TypedDict, TypeVar, Union

ValueChart = TypedDict("ValueChart", {"countCurrent": Union[int, float], "countPrevious": Optional[Union[int, float]]})

DistributionChart = list[TypedDict("DistributionChartEntry", {"key": str, "value": Union[int, float]})]

TimeBasedChart = list[TypedDict("TimeBasedChartEntry", {"label": str, "value": Union[int, float]})]

PercentageChart = Union[int, float]

ObjectiveChart = TypedDict("ObjectiveChart", {"value": Union[int, float], "objective": Optional[Union[int, float]]})

LeaderboardChart = list[TypedDict("LeaderboardChartEntry", {"key": str, "value": Union[int, float]})]

SmartChart = TypeVar("SmartChart")

Chart = Union[
    ValueChart,
    DistributionChart,
    TimeBasedChart,
    PercentageChart,
    ObjectiveChart,
    LeaderboardChart,
    SmartChart,
]
