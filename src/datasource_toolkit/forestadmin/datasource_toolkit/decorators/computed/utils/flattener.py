import sys
from typing import Any, Dict, List, Optional, Union

from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

FlatRecordList: TypeAlias = List[List[Any]]

# To compute the fields in parallel, it is much easier to represent the records as a group of
# arrays, one array per field.
#
# The issue with this transformation is that it is not a bijective function.
#
# When we flatten:
# - { title: 'Foundation', author: { country: null } }
#
# After flattening/unflattening, we don't know if the original record was:
# - { title: 'Foundation', author: { country: null } }
# - { title: 'Foundation', author: null }
#
# This is why we add a special marker to the projection, to keep track of null values.
_MARKER_NAME = "__nullMarker"


# class created to impersonate the comportment of javascript undefined, and '?.' use
class _Undefined:
    def get(self, *args, **kwargs):
        return self

    def __eq__(self, value: object) -> bool:
        return isinstance(value, _Undefined)

    # for debugging
    def __str__(self) -> str:
        return "<undefined>"

    def __repr__(self) -> str:
        return str(self)


def with_null_markers(projection: List[str]) -> List[str]:
    ret = projection[:]

    for path in projection:
        parts = path.split(":")
        for i in range(1, len(parts)):
            value = f"{':'.join(parts[0:i])}:{_MARKER_NAME}"
            if value not in ret:
                ret.append(value)
    return ret


def unflatten(flats: FlatRecordList, projection: List[str]) -> List[RecordsDataAlias]:
    try:
        num_records = len(flats[0])
    except IndexError:
        num_records = 0

    records: List[Dict[str, Any]] = [{} for _ in range(0, num_records)]

    for record_index in range(num_records):
        for path_index, path in enumerate(projection):
            # When a marker is found, the parent is null.
            parts = [*filter(lambda part: part != _MARKER_NAME, path.split(":"))]
            value = flats[path_index][record_index]

            # ignore undefined value # but no undefined in python
            if isinstance(value, _Undefined):
                continue

            # set all others (including null)
            record = records[record_index]
            for part_index, part in enumerate(parts):
                if part_index == len(parts) - 1:
                    record[part] = value
                elif not record.get(part):
                    record[part] = {}
                record = record[part]
    return records


def flatten(records: List[RecordsDataAlias], paths: List[str]) -> FlatRecordList:
    ret: FlatRecordList = []
    for field in paths:
        parts = field.split(":")

        values: List[Optional[Union[str, _Undefined]]] = []
        for record in records:
            value = record
            for part in parts[:-1]:
                if value is None:
                    value = _Undefined()
                else:
                    value = value.get(part, _Undefined())

            # for markers, the value tells us which fields are null so that we can set them.
            if parts[-1] == _MARKER_NAME:
                values.append(None if value is None else _Undefined())
                continue

            values.append((value or {}).get(parts[len(parts) - 1], _Undefined()))
        ret.append(values)
    return ret
