import enum
import json
import sys
from datetime import datetime, timedelta
from numbers import Number
from typing import Any, Callable, Dict, List, Literal, Optional, TypedDict, Union

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from typing_extensions import NotRequired, Self, TypeGuard


class Aggregator(enum.Enum):
    COUNT = "Count"
    SUM = "Sum"
    AVG = "Avg"
    MAX = "Max"
    MIN = "Min"


PlainAggregator = Union[Literal["Count"], Literal["Sum"], Literal["Avg"], Literal["Max"], Literal["Min"]]


class DateOperation(enum.Enum):
    YEAR = "Year"
    MONTH = "Month"
    WEEK = "Week"
    DAY = "Day"


class AggregateResult(TypedDict):
    value: Any
    group: Dict[str, Any]


class Summary(TypedDict):
    group: Dict[str, Any]
    start_count: int
    Count: int
    Sum: int
    Max: Optional[int]
    Min: Optional[int]


class PlainAggregationGroup(TypedDict):
    field: str
    operation: NotRequired[str]


class AggregationGroup(TypedDict):
    field: str
    operation: NotRequired[DateOperation]


class PlainAggregation(TypedDict):
    field: NotRequired[Optional[str]]
    operation: PlainAggregator
    groups: NotRequired[List[PlainAggregationGroup]]


class Aggregation:
    def __init__(self, component: PlainAggregation):
        self.field = component.get("field")
        self.operation = Aggregator(component["operation"])
        self.groups: List[AggregationGroup] = []
        for plain_aggregation_group in component.get("groups", []):
            aggregation_group = AggregationGroup(
                field=plain_aggregation_group["field"],
            )
            if plain_aggregation_group.get("operation"):
                aggregation_group["operation"] = DateOperation(plain_aggregation_group.get("operation"))
            self.groups.append(aggregation_group)

    def __eq__(self: Self, obj: Self) -> bool:
        return (
            self.__class__ == obj.__class__
            and self.field == obj.field
            and self.operation == obj.operation
            and self.groups == obj.groups
        )

    @property
    def projection(self) -> Projection:
        aggregate_fields = [self.field, *[group["field"] for group in self.groups]]
        return Projection(*[field for field in aggregate_fields if field is not None])

    def apply(
        self, records: List[RecordsDataAlias], timezone: str, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        rows = self._format_summaries(self._create_summaries(records, timezone))
        rows = sorted(rows, key=lambda r: r["value"])
        if limit is not None and len(rows) > limit:
            rows = rows[:limit]
        return rows

    def _prefix_handler(self, prefix: str) -> Callable[[str], str]:
        def __prefix(field: str) -> str:
            return f"{prefix}:{field}"

        return __prefix

    def nest(self, prefix: str) -> Self:
        if not prefix or (not self.field and not self.groups):
            return self
        return self.replace_fields(self._prefix_handler(prefix))

    def replace_fields(self, handler: Callable[[str], str]) -> Self:
        result = Aggregation(self._to_plain)
        if result.field:
            result.field = handler(result.field)
        new_groups: List[AggregationGroup] = []
        for group in result.groups:
            new_group: AggregationGroup = {"field": handler(group["field"])}
            if "operation" in group:
                new_group["operation"] = group["operation"]
            new_groups.append(new_group)
        result.groups = new_groups

        return result

    @property
    def _to_plain(self) -> PlainAggregation:
        plain_groups: List[PlainAggregationGroup] = []
        for group in self.groups:
            plain_group: PlainAggregationGroup = {"field": group["field"]}
            if "operation" in group:
                plain_group["operation"] = group["operation"].value
            plain_groups.append(plain_group)
        return {"field": self.field, "operation": self.operation.value, "groups": plain_groups}

    def _format_summaries(self, summaries: List[Summary]) -> List[AggregateResult]:
        if self.operation == Aggregator.AVG:
            results = [
                {"group": summary["group"], "value": summary["Sum"] / summary["Count"]}
                for summary in summaries
                if summary["Count"]
            ]
        else:
            results: List[AggregateResult] = []
            for summary in summaries:
                if self.operation == Aggregator.COUNT and not self.field:
                    value = summary["start_count"]
                else:
                    value = summary[self.operation.value]
                results.append({"group": summary["group"], "value": value})
        return results

    def _create_summaries(self, records: List[RecordsDataAlias], timezone: str) -> List[Summary]:
        grouping: Dict[int, Summary] = {}
        for record in records:
            group = self._create_group(record, timezone)
            unique_key = hash(json.dumps(group, sort_keys=True, default=str))
            try:
                summary = grouping[unique_key]
            except KeyError:
                summary = self._create_summary(group)
            summary = self._update_summary_in_place(summary, record)
            grouping[unique_key] = summary
        return list(grouping.values())

    def _create_summary(self, group: RecordsDataAlias) -> Summary:
        return {
            "group": group,
            "start_count": 0,
            "Count": 0,
            "Sum": 0,
            "Min": None,
            "Max": None,
        }

    def _update_summary_in_place(self, summary: Summary, record: RecordsDataAlias) -> Summary:
        summary["start_count"] += 1  #  count(*)
        if self.field:
            value = RecordUtils.get_field_value(record, self.field)
            if value is not None:
                summary["Count"] += 1  #  count(field)
                if summary["Min"] is None or value < summary["Min"]:
                    summary["Min"] = value
                if summary["Max"] is None or value > summary["Max"]:
                    summary["Max"] = value
            if isinstance(value, Number):
                summary["Sum"] += value
        return summary

    def _create_group(self, record: RecordsDataAlias, timezone: str) -> RecordsDataAlias:
        group_record: RecordsDataAlias = {}
        for group in self.groups:
            group_value = RecordUtils.get_field_value(record, group["field"])
            group_record[group["field"]] = self._apply_date_operation(group_value, group.get("operation"), timezone)
        return group_record

    def _apply_date_operation(self, value: str, operation: Optional[DateOperation], timezone: str) -> str:
        if operation:
            if value[-1] == "Z":
                value = value[:-1]  # Python doesn't handle Z in the isoformat
            dt = datetime.fromisoformat(value).replace(tzinfo=zoneinfo.ZoneInfo(timezone)).date()
            if operation == DateOperation.YEAR:
                return dt.replace(month=1, day=1).isoformat()
            elif operation == DateOperation.MONTH:
                return dt.replace(day=1).isoformat()
            elif operation == DateOperation.DAY:
                return dt.isoformat()
            elif operation == DateOperation.WEEK:
                return (dt - timedelta(days=dt.weekday())).isoformat()
        return value


def is_aggregation(aggregation: Any) -> TypeGuard[Aggregation]:
    return isinstance(aggregation, Aggregation)
