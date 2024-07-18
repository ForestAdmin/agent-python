# pyright: reportMissingModuleSource=false
import enum
import sys
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Set, cast

import pandas as pd
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    Alternative,
    ReplacerAlias,
)

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo


DateCallback = Callable[[datetime, str], datetime]


class Frequency(enum.Enum):
    HOUR = "H"
    DAY = "d"
    WEEK = "W-MON"
    MONTH = "MS"
    QUARTER = "QS"
    YEAR = "YS"


class Interval(NamedTuple):
    start: datetime
    end: datetime


def _get_now() -> datetime:
    return datetime.now(tz=zoneinfo.ZoneInfo("UTC"))


def _start_of(dt: datetime, hour: bool = True) -> datetime:
    kwargs = {"minute": 0, "second": 0, "microsecond": 0}
    if hour:
        kwargs["hour"] = 0
    return dt.replace(**kwargs)


def _compare_replacer(operator: Operator, date_: DateCallback) -> ReplacerAlias:
    def replacer(leaf: ConditionTreeLeaf, tz: zoneinfo.ZoneInfo) -> ConditionTreeLeaf:
        now = _get_now()
        try:
            date.fromisoformat(leaf.value)  # type:ignore
            is_date = True
        except Exception:
            is_date = False
        return leaf.override(
            {
                "operator": operator,
                "value": format(date_(now, leaf.value).astimezone(tz), as_date=is_date),  # type: ignore
            }
        )

    return replacer


def _build_interval(end: datetime, frequency: str, periods: int, tz: zoneinfo.ZoneInfo) -> Interval:
    dates: List[datetime] = []
    end = end.astimezone(zoneinfo.ZoneInfo("UTC"))  # mandatory to avoid the panda issue with zoneinfo
    for dt in pd.date_range(end=end, periods=periods, freq=frequency).to_pydatetime():  # type: ignore
        dt = cast(datetime, dt)
        if frequency != Frequency.HOUR.value:
            dt = _start_of(dt, True).replace(tzinfo=tz)
        else:
            dt = _start_of(dt, False).astimezone(tz)
        dates.append(dt)
    return Interval(start=dates[0], end=end.astimezone(tz) if periods == 1 else dates[1])


def _interval_replacer(
    frequency: Frequency,
    periods: int,
    frequency_prefix: bool = False,
    end: Optional[datetime] = None,
) -> ReplacerAlias:
    def replacer(leaf: ConditionTreeLeaf, tz: zoneinfo.ZoneInfo) -> ConditionTree:
        nonlocal end
        if not end:
            end = _get_now()
        else:
            end = end.replace(tzinfo=tz)

        frequency_value = frequency.value

        if frequency_prefix:
            frequency_value = f"{leaf.value}{frequency_value}"

        interval = _build_interval(end=end, frequency=frequency_value, periods=periods, tz=tz)
        as_date = frequency != Frequency.HOUR
        return ConditionTreeFactory.intersect(
            [
                leaf.override({"operator": Operator.GREATER_THAN, "value": format(interval.start, as_date=as_date)}),
                leaf.override({"operator": Operator.LESS_THAN, "value": format(interval.end, as_date=as_date)}),
            ]
        )

    return replacer


def _from_utc_iso_format(value: str) -> datetime:
    if value[-1] == "Z":
        value = value[:-1]  # Python doesn't handle Z in the isoformat
    return datetime.fromisoformat(value).replace(tzinfo=zoneinfo.ZoneInfo("UTC"))


def _before_to_less_than(now: datetime, value: Any) -> datetime:
    return _from_utc_iso_format(str(value))


def _after_to_greater_than(now: datetime, value: Any) -> datetime:
    return _from_utc_iso_format(str(value))


def _past_to_less_than(now: datetime, value: Any) -> datetime:
    return now


def _future_to_greater_than(
    now: datetime,
    value: Any,
) -> datetime:
    return now


def _before_x_hours_to_less_than(now: datetime, value: Any) -> datetime:
    return now - timedelta(hours=value)


def _after_x_hours_to_greater_than(now: datetime, value: Any) -> datetime:
    return now + timedelta(hours=value)


def compare(operator: Operator, date: DateCallback) -> Alternative:
    return {
        "depends_on": [operator],
        "for_types": [PrimitiveType.DATE, PrimitiveType.DATE_ONLY],
        "replacer": _compare_replacer(operator, date),
    }


def interval(
    frequency: Frequency,
    periods: int,
    frequency_prefix: bool = False,
    end: Optional[datetime] = None,
) -> Alternative:
    return {
        "depends_on": [Operator.LESS_THAN, Operator.GREATER_THAN],
        "for_types": [PrimitiveType.DATE, PrimitiveType.DATE_ONLY],
        "replacer": _interval_replacer(frequency, periods, frequency_prefix, end),
    }


def previous_interval_to_date(
    frequency: Frequency,
    frequency_prefix: bool = False,
    end: Optional[datetime] = None,
    shift: int = 0,
) -> Alternative:
    return interval(frequency, 1 + shift, frequency_prefix, end)


def previous_interval(
    frequency: Frequency,
    frequency_prefix: bool = False,
    end: Optional[datetime] = None,
    shift: int = 0,
) -> Alternative:
    return interval(frequency, 2 + shift, frequency_prefix, end)


def format(value: datetime, as_date=False) -> str:
    utc_datetime: datetime = value.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
    if as_date:
        return utc_datetime.date().isoformat()
    else:
        return utc_datetime.isoformat(timespec="seconds")


def time_transforms(shift: int = 0) -> Dict[Operator, List[Alternative]]:
    return {
        Operator.BEFORE: [
            compare(Operator.LESS_THAN, _before_to_less_than),
        ],
        Operator.AFTER: [compare(Operator.GREATER_THAN, _after_to_greater_than)],
        Operator.PAST: [compare(Operator.LESS_THAN, _past_to_less_than)],
        Operator.FUTURE: [compare(Operator.GREATER_THAN, _future_to_greater_than)],
        Operator.BEFORE_X_HOURS_AGO: [compare(Operator.LESS_THAN, _before_x_hours_to_less_than)],
        Operator.AFTER_X_HOURS_AGO: [compare(Operator.GREATER_THAN, _after_x_hours_to_greater_than)],
        Operator.PREVIOUS_YEAR: [previous_interval(Frequency.YEAR, shift=shift)],
        Operator.PREVIOUS_QUARTER: [previous_interval(Frequency.QUARTER, shift=shift)],
        Operator.PREVIOUS_MONTH: [previous_interval(Frequency.MONTH, shift=shift)],
        Operator.PREVIOUS_WEEK: [previous_interval(Frequency.WEEK, shift=shift)],
        Operator.YESTERDAY: [previous_interval(Frequency.DAY, shift=shift)],
        Operator.PREVIOUS_YEAR_TO_DATE: [previous_interval_to_date(Frequency.YEAR, shift=shift)],
        Operator.PREVIOUS_QUARTER_TO_DATE: [previous_interval_to_date(Frequency.QUARTER, shift=shift)],
        Operator.PREVIOUS_MONTH_TO_DATE: [previous_interval_to_date(Frequency.MONTH, shift=shift)],
        Operator.PREVIOUS_WEEK_TO_DATE: [previous_interval_to_date(Frequency.WEEK, shift=shift)],
        Operator.PREVIOUS_X_DAYS_TO_DATE: [previous_interval_to_date(Frequency.DAY, True, shift=shift)],
        Operator.PREVIOUS_X_DAYS: [previous_interval(Frequency.DAY, True, shift=shift)],
        Operator.TODAY: [
            previous_interval(
                Frequency.DAY,
                end=_start_of(_get_now() + timedelta(days=1)),
                shift=shift,
            )
        ],
    }


SHIFTED_OPERATORS: Set[Operator] = {
    Operator.PREVIOUS_YEAR,
    Operator.PREVIOUS_QUARTER,
    Operator.PREVIOUS_MONTH,
    Operator.PREVIOUS_WEEK,
    Operator.YESTERDAY,
    Operator.PREVIOUS_YEAR_TO_DATE,
    Operator.PREVIOUS_QUARTER_TO_DATE,
    Operator.PREVIOUS_MONTH_TO_DATE,
    Operator.PREVIOUS_WEEK_TO_DATE,
    Operator.TODAY,
}
