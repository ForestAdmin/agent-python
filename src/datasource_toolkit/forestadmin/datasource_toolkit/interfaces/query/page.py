from typing import List, Optional, TypedDict

from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class PlainPage(TypedDict):
    skip: int
    limit: int


class Page:
    def __init__(self, skip: Optional[int] = None, limit: Optional[int] = None):
        self.skip = skip or 0
        self.limit = limit

    def apply(self, records: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        if self.limit:
            return records[self.skip : self.skip + self.limit]
        return records[self.skip :]
