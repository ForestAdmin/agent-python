from typing import Any, Awaitable, Callable, Optional, Union

from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

WriteDefinition = Callable[
    [Any, WriteCustomizationContext], Union[Awaitable[Optional[RecordsDataAlias]], Optional[RecordsDataAlias]]
]
