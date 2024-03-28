from typing import Any, Dict, List, Optional, Set, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.action.types.fields import BaseDynamicField, DynamicField, FieldFactory
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionField, ActionResult, ActionsScope
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


class ActionCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._actions: Dict[str, ActionDict] = {}

    def add_action(self, name: str, action: ActionDict):
        action["form"] = [
            FieldFactory.build(field) if not isinstance(field, BaseDynamicField) else field
            for field in action.get("form", [])
        ]
        self._actions[name] = action
        self.mark_schema_as_dirty()

    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        filter_: Optional[Filter] = None,
    ) -> ActionResult:
        action = self._actions.get(name)
        if not action:
            return await super().execute(caller, name, data, filter_)  # type: ignore

        context = self._get_context(caller, action, data, filter_, None)
        response_builder = ResultBuilder()
        result = await call_user_function(action["execute"], context, response_builder)  # type: ignore
        return cast(
            ActionResult, result or {"type": "Success", "invalidated": set(), "format": "text", "message": "Success"}
        )

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias],
        filter_: Optional[Filter] = None,
        meta: Optional[Dict[str, Any]] = dict(),
    ) -> List[ActionField]:
        action = self._actions.get(name)
        if not action:
            return await super().get_form(caller, name, data, filter_, meta)  # type: ignore
        elif not action.get("form"):
            return []

        form_values = data or {}
        used: Set[str] = set()
        context = self._get_context(caller, action, form_values, filter_, used, meta.get("changed_field"))
        form_fields: List[DynamicField] = cast(List[DynamicField], [field for field in action.get("form", [])])
        if meta.get("search_field"):
            # in the case of a search hook,
            # we don't want to rebuild all the fields. only the one searched
            form_fields = [field for field in form_fields if field.label == meta["search_field"]]

        form_values = await self._build_form_values(context, form_fields, form_values)
        action_fields = await self._build_fields(
            context, form_fields, form_values, meta.get("search_values", {}).get(meta.get("search_field"))
        )
        for field in action_fields:
            field["watch_changes"] = field["label"] in context.form_values.used_keys
        return action_fields

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        actions_schema = {}
        for name, action in self._actions.items():
            dynamics: List[bool] = []
            for field in action.get("form", []):
                dynamics.append(field.is_dynamic)
            actions_schema[name] = Action(
                scope=ActionsScope(action["scope"]),
                generate_file=action.get("generate_file", False),
                static_form=not any(dynamics),
            )
        return {**sub_schema, "actions": actions_schema}

    def _get_context(
        self,
        caller: User,
        action: ActionDict,
        form_values: RecordsDataAlias,
        filter_: Optional[Filter] = None,
        used: Optional[Set[str]] = None,
        changed_field: Optional[str] = None,
    ) -> ActionContext:
        return {
            ActionsScope.SINGLE: ActionContextSingle,
            ActionsScope.BULK: ActionContextBulk,
            ActionsScope.GLOBAL: ActionContext,
        }[ActionsScope(action["scope"])](
            cast(Collection, self), caller, form_values, filter_, used, changed_field  # type: ignore
        )

    async def _build_form_values(
        self, context: ActionContext, fields: List[DynamicField], data: Optional[Dict[str, Any]]
    ):
        if data is None:
            form_values: Dict[str, Any] = {}
        else:
            form_values = {**data}

        for field in fields:
            form_values[field.label] = form_values.get(field.label, await field.default_value(context))

        return form_values

    async def _build_fields(
        self,
        context: ActionContext,
        fields: List[DynamicField],
        form_values: RecordsDataAlias,
        search_value: Optional[str] = None,
    ) -> List[ActionField]:
        action_fields: List[ActionField] = []
        for field in fields:
            if await field.if_(context):
                action_fields.append(await field.to_action_field(context, form_values.get(field.label), search_value))
        return action_fields
