from typing import Any, Callable, Optional

from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)

WriteDefinition = Callable[[Any, WriteCustomizationContext], Optional[Any]]
