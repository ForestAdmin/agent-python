import sys

from forestadmin.datasource_toolkit.utils import removeprefix

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Callable, List, Union

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils


class PlainSortClause(TypedDict):
    field: str
    ascending: bool


ReplaceCallback = Callable[[PlainSortClause], Union["Sort", List[PlainSortClause], PlainSortClause]]


class SortException(DatasourceToolkitException):
    pass


class Sort(list):  # type: ignore
    @property
    def projection(self: List[PlainSortClause]) -> Projection:
        return Projection(*[plain_sort["field"] for plain_sort in self])

    def replace_clauses(self: List[PlainSortClause], callback: "ReplaceCallback"):
        clauses: List[PlainSortClause] = []
        for plain_sort in self:
            clause = callback(plain_sort)
            if isinstance(clause, list):
                clauses.append(*clause)  # type: ignore
            else:
                clauses.append(clause)
        return Sort(clauses)

    def nest(self: List[PlainSortClause], prefix: str) -> List[PlainSortClause]:
        if prefix:
            for plain_sort in self:
                plain_sort["field"] = f'{prefix}:{plain_sort["field"]}'
        return self

    def inverse(self: List[PlainSortClause]) -> List[PlainSortClause]:
        for plain_sort in self:
            plain_sort["ascending"] = not plain_sort["ascending"]
        return self

    def unnest(self: List[PlainSortClause]) -> List[PlainSortClause]:
        splited = self[0]["field"].split(":")
        prefix = splited[0]
        plain_sorts: List[PlainSortClause] = []
        for plain_sort in self:
            if not plain_sort["field"].startswith(prefix):
                raise SortException("Cannot unnest sort")
            plain_sort["field"] = removeprefix(plain_sort["field"], f"{prefix}:")
            plain_sorts.append(plain_sort)
        return Sort(plain_sorts)

    def apply(self: List[PlainSortClause], records: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        for plain_sort in self[::-1]:
            records.sort(
                key=lambda record: RecordUtils.get_field_value(record, plain_sort["field"]),
                reverse=not plain_sort["ascending"],
            )
        return records
