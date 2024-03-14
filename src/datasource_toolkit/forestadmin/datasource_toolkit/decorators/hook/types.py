from typing import Awaitable, Callable, Literal, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.hook.context.hooks import HookContext

THookContext = TypeVar("THookContext", bound=HookContext)


HookHandler = Callable[[THookContext], Union[Awaitable[None], None]]

Position = Literal["Before", "After"]

CrudMethod = Literal["List", "Create", "Update", "Delete", "Aggregate"]
