from datetime import date, datetime
from typing import Dict, List, Optional, Union, cast

import pandas as pd
from forestadmin.datasource_toolkit.interfaces.chart import (
    DistributionChart,
    LeaderboardChart,
    ObjectiveChart,
    PercentageChart,
    SmartChart,
    TimeBasedChart,
    ValueChart,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import DateOperation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import Frequency


class ResultBuilder:
    FREQUENCIES = {"Day": Frequency.DAY, "Week": Frequency.WEEK, "Month": Frequency.MONTH, "Year": Frequency.YEAR}

    FORMATS: Dict[DateOperation, str] = {
        DateOperation.DAY: "%d/%m/%Y",
        DateOperation.WEEK: "W%W-%Y",
        DateOperation.MONTH: "%m %Y",
        DateOperation.YEAR: "%Y",
    }

    @staticmethod
    def value(value: Union[int, float], previous_value: Optional[Union[int, float]] = None) -> ValueChart:
        return ValueChart(countCurrent=value, countPrevious=previous_value)

    @staticmethod
    def distribution(obj: List[tuple[str, Union[int, float]]]) -> DistributionChart:
        return [{"key": item[0], "value": item[1]} for item in obj]

    @classmethod
    def time_based(
        cls, time_range: DateOperation, values: List[Dict[Union[str, date, datetime], Union[int, float]]]
    ) -> TimeBasedChart:
        format_ = cls.FORMATS[time_range]
        formatted = {}

        for _date, value in values.items():
            if isinstance(_date, str):
                date_obj = datetime.fromisoformat(_date).date()
            elif isinstance(_date, date):
                date_obj = _date
            elif isinstance(_date, datetime):
                date_obj = _date.date()
            formatted[date_obj] = formatted.get(date_obj, 0) + value

        first = min(formatted.keys())
        last = max(formatted.keys())
        data_points = []

        for current in pd.date_range(first, last, freq=cls.FREQUENCIES[time_range.value].value):
            label = current.strftime(format_)
            data_points.append(
                {
                    "label": label,
                    "values": {"value": formatted.get(current.date(), 0)},
                }
            )
        return TimeBasedChart(data_points)

    @staticmethod
    def percentage(value: Union[int, float]) -> PercentageChart:
        return value

    @staticmethod
    def objective(value: Union[int, float], objective: Union[int, float]) -> ObjectiveChart:
        return ObjectiveChart(value=value, objective=objective)

    @staticmethod
    def leaderboard(value: List) -> LeaderboardChart:
        return cast(LeaderboardChart, ResultBuilder.distribution(value))

    @staticmethod
    def smart(data) -> SmartChart:
        return data
