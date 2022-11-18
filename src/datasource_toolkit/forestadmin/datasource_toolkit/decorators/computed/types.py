from typing import Any, Awaitable, Callable, List, TypedDict

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import NotRequired


class ComputedDefinition(TypedDict):
    column_type: ColumnAlias
    dependencies: List[str]
    get_values: Callable[[List[RecordsDataAlias], Any], Awaitable[Any]]
    is_required: NotRequired[bool]
    default_value: NotRequired[Any]
    enum_values: NotRequired[List[Any]]
