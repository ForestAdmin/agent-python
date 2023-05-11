import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Any, Awaitable, Callable, List

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
