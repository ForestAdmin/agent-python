from typing import Any, List, Tuple

from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyCollection
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def instances_to_records(
    collection: BaseSqlAlchemyCollection, instances: List[Any]
) -> List[RecordsDataAlias]:
    records: List[RecordsDataAlias] = []
    for instance in instances:
        record: RecordsDataAlias = {}
        for column in collection.mapper.c:  # type: ignore
            record[column.name] = getattr(instance, column.name)
        records.append(record)
    return records


def projections_to_records(
    projection: Projection, items: List[Tuple[Any]]
) -> List[RecordsDataAlias]:
    records: List[RecordsDataAlias] = []
    for item in items:
        result = dict(zip(projection, item))
        record: RecordsDataAlias = {}
        for key in result.keys():
            res: RecordsDataAlias = {}
            if ":" in key:
                for sub_key in key.split(":")[::-1]:
                    if not res or sub_key not in record:
                        value: Any = res or result[key]
                        res = dict(((sub_key, value),))
                    else:
                        record[sub_key] = res
                        break
                else:
                    record.update(res)
            else:
                record[key] = result[key]
        records.append(record)

    return records


def aggregations_to_records(items: List[Tuple[Any]]):
    records: List[RecordsDataAlias] = []
    for item in items:
        records.append(dict(zip(item.keys(), item)))  #  type: ignore
    return records
