# pyright: reportMissingModuleSource=false
import enum
import sys
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, NamedTuple, Optional, cast

import pandas as pd

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)
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


def __get_now() -> datetime:
    return datetime.utcnow().replace(tzinfo=zoneinfo.ZoneInfo("UTC"))


def __start_of(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def __compare_replacer(operator: Operator, date: DateCallback) -> ReplacerAlias:
    def replacer(leaf: ConditionTreeLeaf, tz: str) -> ConditionTreeLeaf:
        now = __get_now()
        return leaf.override({"operator": operator, "value": format(date(now, leaf.value))})

    return replacer


def __build_interval(end: datetime, frequency: str, periods: int, tz: str) -> Interval:

    dates: List[datetime] = []
    for dt in pd.date_range(end=end, periods=periods, freq=frequency).to_pydatetime():  # type: ignore
        dt = cast(datetime, dt)
        if frequency != Frequency.HOUR:
            dt = __start_of(dt).replace(tzinfo=zoneinfo.ZoneInfo(tz))
        dates.append(dt)
    return Interval(start=dates[0], end=end if periods == 1 else dates[1])


def __interval_replacer(
    frequency: Frequency,
    periods: int,
    frequency_prefix: bool = False,
    end: Optional[datetime] = None,
) -> ReplacerAlias:

    if not end:
        end = __get_now()

    def replacer(leaf: ConditionTreeLeaf, tz: str) -> ConditionTree:
        frequency_value = frequency.value

        if frequency_prefix:
            frequency_value = f"{leaf.value}{frequency_value}"

        interval = __build_interval(end=end, frequency=frequency_value, periods=periods, tz=tz)
        return ConditionTreeFactory.intersect(
            [
                leaf.override({"operator": Operator.GREATER_THAN, "value": format(interval.start)}),
                leaf.override({"operator": Operator.LESS_THAN, "value": format(interval.end)}),
            ]
        )

    return replacer


def __from_iso_format(value: str) -> datetime:
    iso_value = value[:-1]  # Python doesn't handle Z in the isoformat
    return datetime.fromisoformat(iso_value).replace(tzinfo=zoneinfo.ZoneInfo("UTC"))


def __before_to_less_than(now: datetime, value: Any) -> datetime:
    return __from_iso_format(value)


def __after_to_greater_than(now: datetime, value: Any) -> datetime:
    return __from_iso_format(value)


def __past_to_less_than(now: datetime, value: Any) -> datetime:
    return now


def __future_to_greater_than(
    now: datetime,
    value: Any,
) -> datetime:
    return now


def __before_x_hours_to_less_than(now: datetime, value: Any) -> datetime:
    return now - timedelta(hours=value)


def __after_x_hours_to_greater_than(now: datetime, value: Any) -> datetime:
    return now + timedelta(hours=value)


def compare(operator: Operator, date: DateCallback) -> Alternative:
    return {
        "depends_on": [operator],
        "for_types": [PrimitiveType.DATE, PrimitiveType.DATE_ONLY],
        "replacer": __compare_replacer(operator, date),
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
        "replacer": __interval_replacer(frequency, periods, frequency_prefix, end),
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


def format(value: datetime) -> str:
    utc_datetime: datetime = value.astimezone(tz=zoneinfo.ZoneInfo("UTC"))
    return utc_datetime.isoformat(timespec="seconds")


def time_transforms(shift: int = 0) -> Dict[Operator, List[Alternative]]:
    return {
        Operator.BEFORE: [
            compare(Operator.LESS_THAN, __before_to_less_than),
        ],
        Operator.AFTER: [compare(Operator.GREATER_THAN, __after_to_greater_than)],
        Operator.PAST: [compare(Operator.LESS_THAN, __past_to_less_than)],
        Operator.FUTURE: [compare(Operator.GREATER_THAN, __future_to_greater_than)],
        Operator.BEFORE_X_HOURS_AGO: [compare(Operator.LESS_THAN, __before_x_hours_to_less_than)],
        Operator.AFTER_X_HOURS_AGO: [compare(Operator.GREATER_THAN, __after_x_hours_to_greater_than)],
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
                end=__start_of(__get_now() + timedelta(days=1)),
                shift=shift,
            )
        ],
    }
