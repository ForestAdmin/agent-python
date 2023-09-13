from typing import Callable, Literal, Union

from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext

HookHandler = Callable[[HookContext], None]

Position = Union[Literal["Before"], Literal["After"]]

CrudMethod = Union[Literal["List"], Literal["Create"], Literal["Update"], Literal["Delete"], Literal["Aggregate"]]
