from typing import Any, Awaitable, Callable, List, Optional, TypedDict

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class ComputedDefinition(TypedDict):
    column_type: ColumnAlias
    dependencies: List[str]
    get_values: Callable[[List[RecordsDataAlias], Any], Awaitable[Any]]
    is_required: Optional[bool]
    default_value: Optional[Any]
    enum_values: Optional[List[Any]]
