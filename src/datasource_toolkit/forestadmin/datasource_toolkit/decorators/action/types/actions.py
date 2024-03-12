from typing import Awaitable, Callable, List, Optional, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.fields import PlainDynamicField
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult, ActionsScope
from typing_extensions import NotRequired, TypedDict


class ActionDict(TypedDict):
    scope: ActionsScope
    generate_file: NotRequired[bool]
    execute: Callable[[ActionContext, ResultBuilder], Union[None, ActionResult, Awaitable[Optional[ActionResult]]]]
    form: NotRequired[List[PlainDynamicField]]
