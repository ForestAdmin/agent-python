import enum
import sys

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from datetime import datetime
from typing import Any, Dict, List, Tuple, cast

from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyCollection
from forestadmin.datasource_sqlalchemy.utils.aggregation import AggregationFactory
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def instances_to_records(collection: BaseSqlAlchemyCollection, instances: List[Any]) -> List[RecordsDataAlias]:
    records: List[RecordsDataAlias] = []
    for instance in instances:
        record: RecordsDataAlias = {}
        for column in collection.mapper.c:  # type: ignore
            record[column.name] = getattr(instance, column.name)
        records.append(record)
    return records


def _cast_value(value: Any, timezone: zoneinfo.ZoneInfo) -> Any:
    if isinstance(value, datetime):
        value = value.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
    return value


def projections_to_records(
    projection: Projection, items: List[Tuple[Any]], timezone: zoneinfo.ZoneInfo
) -> List[RecordsDataAlias]:
    records: List[RecordsDataAlias] = []
    for item in items:
        result = dict(zip(cast(List[str], projection), item))
        record: RecordsDataAlias = dict([(field_name, result[field_name]) for field_name in projection.columns])
        for field_name, sub_fields in projection.relations.items():
            res: Dict[str, Any] = {}
            for sub_field in cast(List[str], sub_fields):
                value = result[f"{field_name}:{sub_field}"]
                if ":" in sub_field:
                    key, *sub_field = sub_field.split(":")
                    if value is not None:
                        for v in cast(List[str], reversed(sub_field)):
                            value = {f"{v}": _cast_value(value, timezone)}
                    res[key] = value
                else:
                    res[sub_field] = value
            else:
                if any(res.values()):
                    record[field_name] = res
                else:
                    record[field_name] = None
        for key in record:
            record[key] = _cast_value(record[key], timezone)
        records.append(record)
    return records


def aggregations_to_records(items: List[Dict[str, Any]]):
    records: List[AggregateResult] = []
    for item in items:
        result = AggregateResult(value=item._mapping[AggregationFactory.LABEL], group={})
        for key in item._mapping.keys():
            if AggregationFactory.GROUP_LABEL in key:
                value = item._mapping[key]
                if isinstance(item._mapping[key], enum.Enum):
                    value = value.value
                result["group"][AggregationFactory.get_field_from_group_field_name(key)] = value
        records.append(result)
    return records
