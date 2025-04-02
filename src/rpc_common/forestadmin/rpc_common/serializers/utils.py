import sys
from enum import Enum
from typing import Any, Dict, Optional, Union

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.interfaces.fields import Operator


def snake_to_camel_case(snake_str: str) -> str:
    ret = "".join(word.title() for word in snake_str.split("_"))
    ret = f"{ret[0].lower()}{ret[1:]}"
    return ret


def camel_to_snake_case(camel_str: str) -> str:
    ret = "".join(f"_{c.lower()}" if c.isupper() else c for c in camel_str)
    return ret


def enum_to_str_or_value(value: Union[Enum, Any]):
    return value.value if isinstance(value, Enum) else value


class OperatorSerializer:
    # OPERATOR_MAPPING: Dict[str, str] = {
    #     "present": "present",
    #     "blank": "blank",
    #     "missing": "missing",
    #     "equal": "equal",
    #     "not_equal": "notEqual",
    #     "less_than": "lessThan",
    #     "greater_than": "greaterThan",
    #     "in": "in",
    #     "not_in": "notIn",
    #     "like": "like",
    #     "starts_with": "startsWith",
    #     "ends_with": "endsWith",
    #     "contains": "contains",
    #     "match": "match",
    #     "not_contains": "notContains",
    #     "longer_than": "longerThan",
    #     "shorter_than": "shorterThan",
    #     "before": "before",
    #     "after": "after",
    #     "after_x_hours_ago": "afterXHoursAgo",
    #     "before_x_hours_ago": "beforeXHoursAgo",
    #     "future": "future",
    #     "past": "past",
    #     "previous_month_to_date": "previousMonthToDate",
    #     "previous_month": "previousMonth",
    #     "previous_quarter_to_date": "previousQuarterToDate",
    #     "previous_quarter": "previousQuarter",
    #     "previous_week_to_date": "previousWeekToDate",
    #     "previous_week": "previousWeek",
    #     "previous_x_days_to_date": "previousXDaysToDate",
    #     "previous_x_days": "previousXDays",
    #     "previous_year_to_date": "previousYearToDate",
    #     "previous_year": "previousYear",
    #     "today": "today",
    #     "yesterday": "yesterday",
    #     "includes_all": "includesAll",
    # }

    @staticmethod
    def deserialize(operator: str) -> Operator:
        return Operator(camel_to_snake_case(operator))
        # for value, serialized in OperatorSerializer.OPERATOR_MAPPING.items():
        #     if serialized == operator:
        #         return Operator(value)
        # raise ValueError(f"Unknown operator: {operator}")

    @staticmethod
    def serialize(operator: Union[Operator, str]) -> str:
        value = operator
        if isinstance(value, Enum):
            value = value.value
        return snake_to_camel_case(value)
        # return OperatorSerializer.OPERATOR_MAPPING[value]


class TimezoneSerializer:
    @staticmethod
    def serialize(timezone: Optional[zoneinfo.ZoneInfo]) -> Optional[str]:
        if timezone is None:
            return None
        return str(timezone)

    @staticmethod
    def deserialize(timezone: Optional[str]) -> Optional[zoneinfo.ZoneInfo]:
        if timezone is None:
            return None
        return zoneinfo.ZoneInfo(timezone)


class CallerSerializer:
    @staticmethod
    def serialize(caller: User) -> Dict:
        return {
            "renderingId": caller.rendering_id,
            "userId": caller.user_id,
            "tags": caller.tags,
            "email": caller.email,
            "firstName": caller.first_name,
            "lastName": caller.last_name,
            "team": caller.team,
            "timezone": TimezoneSerializer.serialize(caller.timezone),
            "request": {"ip": caller.request["ip"]},
        }

    @staticmethod
    def deserialize(caller: Dict) -> User:
        if caller is None:
            return None
        return User(
            rendering_id=caller["renderingId"],
            user_id=caller["userId"],
            tags=caller["tags"],
            email=caller["email"],
            first_name=caller["firstName"],
            last_name=caller["lastName"],
            team=caller["team"],
            timezone=TimezoneSerializer.deserialize(caller["timezone"]),  # type:ignore
            request={"ip": caller["request"]["ip"]},
        )
