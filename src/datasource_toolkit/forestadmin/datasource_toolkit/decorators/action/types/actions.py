from typing import Callable, List, TypedDict, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.fields import PlainDynamicField
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult, ActionsScope

Context = TypeVar("Context", bound=ActionContext)


class ActionDict(TypedDict):
    scope: ActionsScope
    generate_file: bool
    execute: Callable[[Context, ResultBuilder], Union[None, ActionResult]]
    form: List[PlainDynamicField]
