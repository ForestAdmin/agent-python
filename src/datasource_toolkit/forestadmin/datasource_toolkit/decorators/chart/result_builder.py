import enum
from datetime import date, datetime
from typing import Dict, List, Optional, TypedDict, Union

import pandas as pd
from forestadmin.datasource_toolkit.interfaces.chart import (
    DistributionChart,
    LeaderboardChart,
    MultipleTimeBasedChart,
    ObjectiveChart,
    PercentageChart,
    SmartChart,
    TimeBasedChart,
    ValueChart,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import DateOperation, DateOperationLiteral
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import Frequency


class _DateRangeFrequency(enum.Enum):
    Day: str = "days"
    Week: str = "weeks"
    Month: str = "months"
    Year: str = "years"


MultipleTimeBasedLines = List[TypedDict("Line", {"label": str, "values": List[Union[int, float, None]]})]


def _parse_date(date_input: Union[str, date, datetime]) -> date:
    if isinstance(date_input, str):
        return datetime.fromisoformat(date_input).date()
    elif isinstance(date_input, datetime):
        return date_input.date()
    elif isinstance(date_input, date):
        return date_input


def _make_formatted_date_range(
    first: Union[date, datetime], last: Union[date, datetime], frequency: _DateRangeFrequency, format_: str
):
    current = first
    used = set()
    while current <= last:
        yield current.strftime(format_)
        used.add(current.strftime(format_))
        current = (current + pd.DateOffset(**{frequency.value: 1})).date()

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
        cls,
        time_range: Union[DateOperation, DateOperationLiteral],
        values: Dict[Union[str, date, datetime], Union[int, float]],
    ) -> TimeBasedChart:
        """Add a TimeBasedChart based on a time range and a set of values

        Args:
            time_range (DateOperation): The time range for the chart, specified as a DateOperation
            values (Dict[Union[str, date, datetime], Union[int, float]]): This can be an array of objects with 'date'
                and 'value' properties, or a record (object) with date-value pairs

        Returns:
            TimeBasedChart: a TimeBasedChart representing the data within the specified time range

        Example:
            ResultBuilder.time_based(DateOperation.DAY, [
                {"date": "2023-01-01", "value": 42},
                {"date": date(2023, 1, 2), "value": 55},
                {"date": datetime(2023, 1, 3), "value": None},
            ])
        """
        formatted = []
        for _date, value in values.items():
            formatted.append({"date": _date, "value": value})

        return ResultBuilder._build_time_base_chart_result(DateOperation(time_range), formatted)

    @classmethod
    def multiple_time_based(
        cls,
        time_range: Union[DateOperation, DateOperationLiteral],
        dates: List[Union[str, date, datetime]],
        lines: MultipleTimeBasedLines,
    ) -> MultipleTimeBasedChart:
        """Add a MultipleTimeBasedChart based on a time range, an array of dates, and multiple lines of data.

        Args:
            time_range (DateOperation): The time range for the chart, specified as a DateOperation
            dates (List[Union[str, date, datetime]]): An array of dates that define the x-axis values for the chart.
            lines (MultipleTimeBasedLines): An array of lines, each containing a label and an array of numeric data
                values (or None) corresponding to the dates.

        Returns:
            MultipleTimeBasedChart: a MultipleTimeBasedChart representing multiple lines of data within the specified
                time range

        Example:
            ResultBuilder.multiple_time_based(DateOperation.DAY, [
                "2023-01-01", date(2023, 1, 2), datetime(2023, 1, 3)
            ],[
                {"label": "line1", "value": [1, 2, 3]},
                {"label": "line2", "value": [3, 4, None]},
            ])
        """
        if not dates or not lines:
            return {"labels": None, "values": None}

        formatted_lines = []
        formatted_times = None
        for line in lines:
            values = []
            for idx, _date in enumerate(dates):
                values.append({"date": _date, "value": line["values"][idx]})
            build_time_base = ResultBuilder._build_time_base_chart_result(DateOperation(time_range), values)

            if formatted_times is None:
                formatted_times = [time_based["label"] for time_based in build_time_base]

            formatted_lines.append(
                {"key": line["label"], "values": [time_base["values"]["value"] for time_base in build_time_base]}
            )
        return {"labels": formatted_times, "values": formatted_lines}

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

    @staticmethod
    def _build_time_base_chart_result(
        time_range: Union[DateOperation, DateOperationLiteral],
        points: List[Dict[Union[date, datetime, str], Union[int, float, None]]],
    ) -> TimeBasedChart:
        """Normalize the time based chart result to have a value for each time range.
        For example, if the time range is 'Month' and the values are:
            [
                # YYYY-MM-DD
                { "date": date('2022-01-07'), "value": 1 }, # Jan 22
                { "date": date('2022-02-02'), "value": 2 }, # Feb 22
                { "date": date('2022-01-01'), "value": 3 }, # Jan 22
                { "date": date('2022-02-01'), "value": 4 }, # Feb 22
            ]
            The result will be:
            [
                { "label": 'Jan 22', "values": { "value": 4 } },
                { "label": 'Feb 22', "values": { "value": 6 } },
            ]
        """
        if len(points) == 0:
            return []
        points_in_date_time = [{"date": _parse_date(point["date"]), "value": point["value"]} for point in points]
        format_ = ResultBuilder.FORMATS[DateOperation(time_range)]

        formatted = {}
        for point in points_in_date_time:
            label = point["date"].strftime(format_)
            if point["value"] is not None:
                formatted[label] = formatted.get(label, 0) + point["value"]

        data_points = []
        dates = sorted([p["date"] for p in points_in_date_time])
        first = dates[0]
        last = dates[-1]
        for label in _make_formatted_date_range(
            first, last, _DateRangeFrequency[DateOperation(time_range).value], format_
        ):
            data_points.append({"label": label, "values": {"value": formatted.get(label, 0)}})
        return data_points
