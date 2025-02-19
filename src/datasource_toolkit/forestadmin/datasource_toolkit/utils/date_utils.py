from datetime import date, datetime
from typing import Callable, Dict, Iterator, Union

import pandas as pd
from forestadmin.datasource_toolkit.interfaces.query.aggregation import DateOperation

DATE_OPERATION_STR_FORMAT_FN: Dict[DateOperation, Callable[[Union[date, datetime]], str]] = {
    DateOperation.DAY: lambda d: d.strftime("%d/%m/%Y"),
    DateOperation.WEEK: lambda d: d.strftime("W%V-%G"),
    DateOperation.MONTH: lambda d: d.strftime("%b %Y"),
    DateOperation.YEAR: lambda d: d.strftime("%Y"),
    DateOperation.QUARTER: lambda d: f"Q{pd.Timestamp(d).quarter}-{d.year}",
}

_DATE_OPERATION_OFFSET: Dict[DateOperation, pd.DateOffset] = {
    DateOperation.YEAR: pd.DateOffset(years=1),
    DateOperation.QUARTER: pd.DateOffset(months=3),
    DateOperation.MONTH: pd.DateOffset(months=1),
    DateOperation.WEEK: pd.DateOffset(weeks=1),
    DateOperation.DAY: pd.DateOffset(days=1),
}


def parse_date(date_input: Union[str, date, datetime]) -> date:
    if isinstance(date_input, str):
        return datetime.fromisoformat(date_input).date()
    elif isinstance(date_input, datetime):
        return date_input.date()
    elif isinstance(date_input, date):
        return date_input


def make_formatted_date_range(
    first: Union[date, datetime],
    last: Union[date, datetime],
    date_operation: DateOperation,
) -> Iterator[str]:
    current = first
    used = set()
    format_fn = DATE_OPERATION_STR_FORMAT_FN[date_operation]

    while current <= last:
        formatted = format_fn(current)
        yield formatted
        used.add(formatted)
        current = (current + _DATE_OPERATION_OFFSET[date_operation]).date()

    if format_fn(last) not in used:
        yield format_fn(last)
