import enum
from datetime import date, datetime
from typing import Dict, Optional, Union

from dateutil.relativedelta import relativedelta
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


class _DateRangeFrequency(enum.Enum):
    Day: str = "days"
    Week: str = "weeks"
    Month: str = "months"
    Year: str = "years"


def _make_formatted_date_range(
    first: Union[date, datetime], last: Union[date, datetime], frequency: _DateRangeFrequency, format_: str
):
    current = first
    used = set()
    while current <= last:
        yield current.strftime(format_)
        used.add(current.strftime(format_))
        current = current + relativedelta(**{frequency.value: 1})

    if last.strftime(format_) not in used:
        yield last.strftime(format_)


class ResultBuilder:
    FREQUENCIES = {"Day": Frequency.DAY, "Week": Frequency.WEEK, "Month": Frequency.MONTH, "Year": Frequency.YEAR}

    FORMATS: Dict[DateOperation, str] = {
        DateOperation.DAY: "%d/%m/%Y",
        DateOperation.WEEK: "W%V-%Y",
        DateOperation.MONTH: "%b %Y",
        DateOperation.YEAR: "%Y",
    }

    @staticmethod
    def value(value: Union[int, float], previous_value: Optional[Union[int, float]] = None) -> ValueChart:
        return ValueChart(countCurrent=value, countPrevious=previous_value)

    @staticmethod
    def distribution(obj: Dict[str, Union[int, float]]) -> DistributionChart:
        return [{"key": key, "value": value} for key, value in obj.items()]

    @classmethod
    def time_based(
        cls, time_range: DateOperation, values: Dict[Union[str, date, datetime], Union[int, float]]
    ) -> TimeBasedChart:
        format_ = cls.FORMATS[time_range]
        dates = set()
        formatted = {}

        for _date, value in values.items():
            if isinstance(_date, str):
                date_obj = datetime.fromisoformat(_date).date()
            elif isinstance(_date, datetime):
                date_obj = _date.date()
            elif isinstance(_date, date):
                date_obj = _date
            label = date_obj.strftime(format_)
            dates.add(date_obj)

            formatted[label] = formatted.get(label, 0) + value

        first = min(dates)
        last = max(dates)

        data_points = []
        for label in _make_formatted_date_range(first, last, _DateRangeFrequency[time_range.value], format_):
            data_points.append(
                {
                    "label": label,
                    "values": {"value": formatted.get(label, 0)},
                }
            )
        return data_points

    @staticmethod
    def percentage(value: Union[int, float]) -> PercentageChart:
        return value

    @staticmethod
    def objective(value: Union[int, float], objective: Union[int, float]) -> ObjectiveChart:
        return ObjectiveChart(value=value, objective=objective)

    @staticmethod
    def leaderboard(values: Dict[str, Union[int, float]]) -> LeaderboardChart:
        return sorted([{"key": key, "value": value} for key, value in values.items()], key=lambda x: x["value"])

    @staticmethod
    def smart(data) -> SmartChart:
        return data
