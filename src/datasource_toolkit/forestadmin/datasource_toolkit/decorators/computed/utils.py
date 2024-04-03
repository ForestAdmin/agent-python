import json
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional

from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

Input: TypeAlias = Any
Output: TypeAlias = Any
FlatRecordList: TypeAlias = List[List[Any]]


async def transform_unique_values(inputs: Input, callback: Callable[[List[Input]], Awaitable[List[Output]]]):
    indexes: Dict[int, int] = {}
    mapping: List[int] = []
    unique_inputs: List[Input] = []

    for _input in inputs:
        if _input is not None:
            if isinstance(_input, dict):
                hsh = hash(json.dumps(_input, default=str))
            else:
                hsh = hash(_input)
            if hsh not in indexes:
                indexes[hsh] = len(unique_inputs)
                unique_inputs.append(_input)
            mapping.append(indexes[hsh])
        else:
            mapping.append(-1)

    unique_outputs = await callback(unique_inputs)
    outputs: List[Output] = []

    for idx in mapping:
        if idx != -1:
            outputs.append(unique_outputs[idx])
        else:
            outputs.append(None)

    return outputs


def unflatten(flats: FlatRecordList, projection: Projection) -> List[Optional[RecordsDataAlias]]:
    try:
        num_records = len(flats[0])
    except IndexError:
        num_records = 0

    records: List[Dict[str, Any]] = [{} for _ in range(0, num_records)]

    for column in projection.columns:
        path_index: int = projection.index(column)  # type: ignore
        for idx, value in enumerate(flats[path_index]):
            records[idx][column] = value

    for relation, paths in projection.relations.items():
        sub_flats = [flats[projection.index(f"{relation}:{path}")] for path in paths]  # type: ignore
        sub_records = unflatten(sub_flats, paths)
        for idx in range(len(records)):
            records[idx][relation] = sub_records[idx]

    res: List[Optional[RecordsDataAlias]] = []
    for record in records:
        if any(record.values()):
            res.append(record)
        else:
            res.append(None)
    return res


def flatten(records: List[Optional[RecordsDataAlias]], projection: List[str]) -> FlatRecordList:
    res: FlatRecordList = []
    for field_name in projection:
        values: List[Optional[str]] = []
        for record in records:
            if record:
                values.append(RecordUtils.get_field_value(record, field_name))
            else:
                values.append(None)
        res.append(values)
    return res
