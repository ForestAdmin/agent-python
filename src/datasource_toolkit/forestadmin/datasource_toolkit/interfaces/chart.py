from typing import Dict, List, Optional, TypedDict, TypeVar, Union

ValueChart = TypedDict("ValueChart", {"countCurrent": Union[int, float], "countPrevious": Optional[Union[int, float]]})

DistributionChart = List[TypedDict("DistributionChartEntry", {"key": str, "value": Union[int, float]})]

TimeBasedChart = List[TypedDict("TimeBasedChartEntry", {"label": str, "values": Dict[str, Union[int, float]]})]

MultipleTimeBasedChart = TypedDict(
    "MultipleTimeBasedChart",
    {
        "labels": List[str],
        "values": List[TypedDict("MultipleTimeBasedChartEntry", {"key": str, "values": List[Union[int, float]]})],
    },
)

PercentageChart = Union[int, float]

ObjectiveChart = TypedDict("ObjectiveChart", {"value": Union[int, float], "objective": Optional[Union[int, float]]})

LeaderboardChart = List[TypedDict("LeaderboardChartEntry", {"key": str, "value": Union[int, float]})]

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

a: TimeBasedChart = [{"label": "&", "values": {"value"}}]
