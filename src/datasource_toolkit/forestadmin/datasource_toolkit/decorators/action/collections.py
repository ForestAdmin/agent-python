from typing import Any, Dict, List, Optional, Set, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    BaseDynamicField,
    DynamicField,
    FieldFactory,
    FormElement,
    LayoutDynamicField,
)
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.actions import (
    Action,
    ActionField,
    ActionFieldType,
    ActionResult,
    ActionsScope,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


class ActionCollectionException(Exception):
    pass


class ActionCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._actions: Dict[str, ActionDict] = {}

    def add_action(self, name: str, action: ActionDict):
        if "form" in action and "pages" in action:
            raise ActionCollectionException("Cannot have 'pages' and 'form' in the same action.")

        if "form" in action:
            action["form"] = [
                FieldFactory.build(field) if not isinstance(field, BaseDynamicField) else field
                for field in action.get("form", [])
            ]
        if "pages" in action:
            for page_nb, page in enumerate(action["pages"]):
                action["pages"][page_nb]["form"] = [
                    FieldFactory.build(field) if not isinstance(field, BaseDynamicField) else field
                    for field in page.get("form", [])
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
        elif "form" not in action:
            return []

        form_values = data or {}
        used: Set[str] = set()
        context = self._get_context(caller, action, form_values, filter_, used, meta.get("changed_field"))
        # TODO: need to know the structure in http request. For now let's consider it's like now, and the agent convert name into pages
        form_fields: List[DynamicField] = cast(List[DynamicField], [field for field in action.get("form", [])])

        if meta.get("search_field"):
            # in the case of a search hook,
            # we don't want to rebuild all the fields. only the one searched
            form_fields = [field for field in form_fields if field.label == meta["search_field"]]

        form_values = await self._build_form_values(context, form_fields, form_values)
        action_fields = await self._build_fields(
            context, form_fields, form_values, meta.get("search_values", {}).get(meta.get("search_field"))
        )

        self._add_hook_to_fields(context, action_fields)
        return action_fields

    def _add_hook_to_fields(self, context: ActionContext, fields: List[ActionField]):
        for field in fields:
            if field["type"] != ActionFieldType.LAYOUT:
                field["watch_changes"] = field["label"] in context.form_values.used_keys
            elif field["widget"] == "Page":
                self._add_hook_to_fields(context, field["elements"])
            elif field["widget"] == "Row":
                self._add_hook_to_fields(context, field["fields"])

    # async def _get_multipage_form(
    #     self,
    #     caller: User,
    #     name: str,
    #     data: Optional[RecordsDataAlias],
    #     filter_: Optional[Filter] = None,
    #     meta: Optional[Dict[str, Any]] = dict(),
    # ) -> List[ActionPage]:
    #     action = self._actions.get(name)
    #     form_values = data or {}
    #     used: Set[str] = set()
    #     context = self._get_context(caller, action, form_values, filter_, used, meta.get("changed_field"))
    #     # TODO: need to know the structure in http request. For now let's consider it's like now, and the agent convert name into pages
    #     form_fields: List[DynamicField] = cast(
    #         List[DynamicField], [field for page in action.get("pages", []) for field in page.get("form", [])]
    #     )
    #     pages_fields = [[field for field in page.get("form", [])] for page in action.get("pages", [])]
    #     if meta.get("search_field"):
    #         # in the case of a search hook,
    #         # we don't want to rebuild all the fields. only the one searched
    #         form_fields = [field for field in form_fields if field.label == meta["search_field"]]

    #     form_values = await self._build_form_values(context, form_fields, form_values)
    #     pages_fields: List[ActionPage] = []
    #     for page in action.get("pages", []):
    #         new_page: ActionPage = {
    #             "next_button_label": page.get("next_button_label"),
    #             "back_button_label": page.get("back_button_label"),
    #             "form": [],
    #         }  # type: ignore

    #         for label in ["next_button_label", "back_button_label"]:
    #             if callable(new_page[label]):
    #                 new_page[label] = await call_user_function(new_page[label])

    #         fields_names = [f.label for f in page.get("form", [])]
    #         new_page["form"] = await self._build_fields(
    #             context,
    #             [f for f in form_fields if f.label in fields_names],
    #             form_values,
    #             meta.get("search_values", {}).get(meta.get("search_field")),
    #         )
    #         for field in new_page["form"]:
    #             field["watch_changes"] = field["label"] in context.form_values.used_keys
    #         pages_fields.append(new_page)
    #     return pages_fields

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        actions_schema = {}
        for name, action in self._actions.items():
            dynamics: List[bool] = []
            for field in action.get("form", []):
                dynamics.append(field.is_dynamic)

            actions_schema[name] = Action(
                scope=ActionsScope(action["scope"]),
                description=action.get("description"),
                submit_button_label=action.get("submit_button_label"),
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
        self, context: ActionContext, fields: List[FormElement], data: Optional[Dict[str, Any]]
    ):
        if data is None:
            form_values: Dict[str, Any] = {}
        else:
            form_values = {**data}

        for field in fields:
            if isinstance(field, DynamicField):
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
                value = None if isinstance(field, LayoutDynamicField) else form_values.get(field.label)
                action_fields.append(await field.to_action_field(context, value, search_value))
        return action_fields
