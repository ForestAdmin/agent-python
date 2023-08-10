import sys
from typing import Callable, Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext

HookHandler = Callable[[HookContext], None]

Position = Union[Literal["Before"], Literal["After"]]

CrudMethod = Union[Literal["List"], Literal["Create"], Literal["Update"], Literal["Delete"], Literal["Aggregate"]]
