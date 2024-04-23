from typing import Awaitable, Callable, List, Union

from forestadmin.datasource_toolkit.decorators.override.context import (
    CreateOverrideCustomizationContext,
    DeleteOverrideCustomizationContext,
    UpdateOverrideCustomizationContext,
)
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

CreateOverrideHandler = Callable[
    [CreateOverrideCustomizationContext], Union[Awaitable[List[RecordsDataAlias]], List[RecordsDataAlias]]
]

UpdateOverrideHandler = Callable[[UpdateOverrideCustomizationContext], Union[Awaitable[None], None]]

DeleteOverrideHandler = Callable[[DeleteOverrideCustomizationContext], Union[Awaitable[None], None]]
