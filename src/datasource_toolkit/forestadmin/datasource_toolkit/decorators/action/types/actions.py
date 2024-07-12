from typing import Awaitable, Callable, List, Optional, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.fields import BaseDynamicField, PlainDynamicField
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult, ActionScopeLiteral, ActionsScope
from typing_extensions import NotRequired, TypedDict

ActionExecute = Union[
    Callable[
        [ActionContext, ResultBuilder],
        Union[Optional[ActionResult], Awaitable[Optional[ActionResult]]],
    ],
    Callable[
        [ActionContextSingle, ResultBuilder],
        Union[Optional[ActionResult], Awaitable[Optional[ActionResult]]],
    ],
    Callable[
        [ActionContextBulk, ResultBuilder],
        Union[Optional[ActionResult], Awaitable[Optional[ActionResult]]],
    ],
]


class ActionDict(TypedDict):
    scope: Union[ActionsScope, ActionScopeLiteral]
    generate_file: NotRequired[bool]
    execute: ActionExecute
    form: NotRequired[List[Union[PlainDynamicField, BaseDynamicField]]]
