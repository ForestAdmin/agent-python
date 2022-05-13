from typing import Callable, List, TypedDict, Union

from typing_extensions import Self

from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils


class PlainSortClause(TypedDict):
    field: str
    ascending: bool


ReplaceCallback = Callable[[PlainSortClause], Union["Sort", List[PlainSortClause], PlainSortClause]]


class Sort(list[PlainSortClause]):
    @property
    def projection(self) -> Projection:
        return Projection([plain_sort["field"] for plain_sort in self])

    def replace_clauses(self, callback: "ReplaceCallback"):
        clauses: List[PlainSortClause] = []
        for plain_sort in self:
            clause = callback(plain_sort)
            if isinstance(clause, list):
                clauses.append(*clause)
            else:
                clauses.append(clause)
        return Sort(*clauses)

    def nest(self, prefix: str) -> Self:
        if prefix:
            for plain_sort in self:
                plain_sort["field"] = f'{prefix}:{plain_sort["field"]}'
        return self

    def inverse(self) -> Self:
        for plain_sort in self:
            plain_sort["ascending"] = not plain_sort["ascending"]
        return self

    def unnest(self) -> Self:
        prefix, _ = self[0]["field"].split(":")
        for plain_sort in self:
            if not plain_sort["field"].startswith(prefix):
                raise
            plain_sort["field"].removeprefix(f"{prefix}:")
        return self

    def apply(self, records: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        for plain_sort in self:
            records.sort(
                key=lambda record: RecordUtils.get_field_value(record, plain_sort["field"]),
                reverse=not plain_sort["ascending"],
            )
        return records
