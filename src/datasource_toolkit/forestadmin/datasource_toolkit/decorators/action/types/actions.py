import abc
from typing import Callable, Generic, List, Sequence, TypedDict, TypeVar, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.fields import DynamicField, FieldFactory, PlainDynamicField
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult, ActionsScope

Context = TypeVar("Context", bound=ActionContext)


class ActionDict(TypedDict):
    scope: ActionsScope
    generate_file: bool
    execute: Callable[[Context, ResultBuilder], Union[None, ActionResult]]
    form: List[PlainDynamicField]


# TODO: remove this one when removing deprecation of class style actions


class BaseAction(Generic[Context]):
    SCOPE: ActionsScope
    FORM: Sequence[PlainDynamicField] = []
    GENERATE_FILE: bool = False

    def __init__(self):
        ForestLogger.log(
            "warning",
            f"{self.__class__} Using action class is deprecated (ActionSingle, ActionBulk or ActionGlobal). "
            + "Please use the dict syntax instead (doc: "
            + "https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/actions).",
        )
        self.form = self._build_form(self.FORM)  # type: ignore

    @abc.abstractmethod
    async def execute(self, context: Context, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        """The main function of the action"""

    def _build_form(self, plain_fields: Sequence[PlainDynamicField]) -> List[DynamicField[Context]]:
        form: List[DynamicField[Context]] = []
        for plain_field in plain_fields:
            form.append(FieldFactory[Context].build(plain_field))
        return form

    def to_dict(self) -> ActionDict:
        return ActionDict(scope=self.SCOPE, generate_file=self.GENERATE_FILE, execute=self.execute, form=self.form)


class ActionSingle(BaseAction[ActionContextSingle]):
    SCOPE = ActionsScope.SINGLE


class ActionBulk(BaseAction[ActionContextBulk]):
    SCOPE = ActionsScope.BULK


class ActionGlobal(BaseAction[ActionContext]):
    SCOPE = ActionsScope.GLOBAL


ActionAlias = Union[ActionSingle, ActionBulk, ActionGlobal, ActionDict]
