from typing import Any, Dict, List, Tuple

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


def projections_to_records(projection: Projection, items: List[Tuple[Any]]) -> List[RecordsDataAlias]:
    records: List[RecordsDataAlias] = []
    for item in items:
        result = dict(zip(projection, item))
        record: RecordsDataAlias = dict([(field_name, result[field_name]) for field_name in projection.columns])
        for field_name, sub_fields in projection.relations.items():
            res: Dict[str, Any] = {}
            for sub_field in sub_fields:
                res[sub_field] = result[f"{field_name}:{sub_field}"]
            else:
                if any(res.values()):
                    record[field_name] = res
                else:
                    record[field_name] = None
        records.append(record)
    return records


def aggregations_to_records(items: List[Dict[str, Any]]):
    records: List[AggregateResult] = []
    for item in items:
        records.append(AggregateResult(value=item[AggregationFactory.LABEL], group={}))
    return records
