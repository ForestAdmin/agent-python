from typing import Any, Awaitable, Callable, List, Optional, Union

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import NotRequired, TypedDict


class ComputedDefinition(TypedDict):
    column_type: ColumnAlias
    dependencies: List[str]
    get_values: Callable[
        [List[RecordsDataAlias], CollectionCustomizationContext], Union[List[Any], Awaitable[List[Any]]]
    ]
    is_required: NotRequired[Optional[bool]]
    default_value: NotRequired[Optional[Any]]
    enum_values: NotRequired[Optional[List[Any]]]
