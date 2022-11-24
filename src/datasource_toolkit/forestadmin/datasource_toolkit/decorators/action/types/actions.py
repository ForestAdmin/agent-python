import abc
from typing import Generic, List, Sequence, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.fields import DynamicField, FieldFactory, PlainDynamicField
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult, ActionsScope

Context = TypeVar("Context", bound=ActionContext)


class BaseAction(Generic[Context]):

    SCOPE: ActionsScope
    FORM: Sequence[PlainDynamicField] = []
    GENERATE_FILE: bool = False

    def __init__(self):
        self.form = self._build_form(self.FORM)  # type: ignore

    @abc.abstractmethod
    async def execute(self, context: Context, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        pass

    def _build_form(self, plain_fields: Sequence[PlainDynamicField]) -> List[DynamicField[Context]]:
        form: List[DynamicField[Context]] = []
        for plain_field in plain_fields:
            form.append(FieldFactory[Context].build(plain_field))
        return form


class ActionSingle(BaseAction[ActionContextSingle]):
    SCOPE = ActionsScope.SINGLE


class ActionBulk(BaseAction[ActionContextBulk]):
    SCOPE = ActionsScope.BULK


class ActionGlobal(BaseAction[ActionContext]):
    SCOPE = ActionsScope.GLOBAL


ActionAlias = Union[ActionSingle, ActionBulk, ActionGlobal]
