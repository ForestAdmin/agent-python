from typing import Any, Callable, Dict, List, Optional, Set, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import (
    ActionAlias,
    ActionBulk,
    ActionGlobal,
    ActionSingle,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import DynamicField
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class ActionMixin:
    datasource: property
    mark_schema_as_dirty: Callable[..., None]

    def __init__(self, *args: Any, **kwargs: Any):
        super(ActionMixin, self).__init__(*args, **kwargs)
        self._actions: Dict[str, ActionAlias] = {}

    def add_action(self, name: str, action: ActionAlias):
        self._actions[name] = action
        self.mark_schema_as_dirty()

    async def execute(
        self,
        name: str,
        data: RecordsDataAlias,
        filter: Optional[Filter],
    ) -> ActionResult:
        action = self._actions[name]
        if not action:
            return super(ActionMixin, self).execute(name, data, filter)  # type: ignore

        context = self._get_context(action, data, filter)
        response_builder = ResultBuilder()
        result = await action.execute(context, response_builder)  # type: ignore
        return result or {"type": "Success", "invalidated": set(), "format": "text", "message": "Success"}

    async def get_form(
        self, name: str, data: Optional[RecordsDataAlias], filter: Optional[Filter]
    ) -> List[ActionField]:
        action = self._actions.get(name)
        if not action:
            return super(ActionMixin, self).get_form(name, data, filter)  # type: ignore
        elif not action.form:
            return []

        form_values = data or {}
        used: Set[str] = set()
        context = self._get_context(action, form_values, filter, used)
        form_fields: List[DynamicField[ActionContext]] = cast(
            List[DynamicField[ActionContext]], [field for field in action.form]
        )

        form_values = await self._build_form_values(context, form_fields, form_values)
        action_fields = await self._build_fields(context, form_fields, form_values)
        for field in action_fields:
            field["watch_changes"] = field["label"] in context.form_values.used_keys
        return action_fields

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(ActionMixin, self).schema  # type: ignore
        for name, action in self._actions.items():
            dynamics: List[bool] = []
            for field in action.form or []:
                dynamics.append(field.is_dynamic)
            schema["actions"][name] = Action(
                scope=action.SCOPE, generate_file=action.GENERATE_FILE, static_form=not any(dynamics)
            )

        return schema

    def _get_context(
        self,
        action: Union[ActionSingle, ActionBulk, ActionGlobal],
        form_values: RecordsDataAlias,
        filter: Optional[Filter],
        used: Optional[Set[str]] = None,
    ) -> ActionContext:
        return {
            ActionSingle.SCOPE: ActionContextSingle,
            ActionBulk.SCOPE: ActionContextBulk,
            ActionGlobal.SCOPE: ActionContext,
        }[action.SCOPE](
            cast(Collection, self), form_values, filter, used  # type: ignore
        )

    async def _build_form_values(
        self, context: ActionContext, fields: List[DynamicField[ActionContext]], data: Optional[Dict[str, Any]]
    ):
        if data is None:
            form_values: Dict[str, Any] = {}
        else:
            form_values = {**data}

        for field in fields:
            form_values[field.label] = form_values.get(field.label, await field.default_value(context))

        return form_values

    async def _build_fields(
        self, context: ActionContext, fields: List[DynamicField[ActionContext]], form_values: RecordsDataAlias
    ) -> List[ActionField]:
        action_fields: List[ActionField] = []
        for field in fields:
            if await field.if_(context):
                action_fields.append(await field.to_action_field(context, form_values.get(field.label)))  # type: ignore
        return action_fields
