from typing import Any, Dict, List, Optional, Set, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.form_elements import (
    BaseDynamicField,
    BaseDynamicFormElement,
    DynamicFormElements,
    DynamicLayoutElements,
    FormElementFactory,
)
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import (
    Action,
    ActionField,
    ActionFieldType,
    ActionFormElement,
    ActionLayoutElement,
    ActionResult,
    ActionsScope,
    BaseActionFormElement,
)
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
            FormElementFactory.build(field) if not isinstance(field, BaseDynamicFormElement) else field
            for field in action.get("form", [])
        ]
        self._validate_id_uniqueness(action["form"])  # type:ignore
        self._validate_root_only_or_no_pages(action["form"], name)  # type:ignore

        self._actions[name] = action
        self.mark_schema_as_dirty()

    def _validate_root_only_or_no_pages(self, form_elements: List[DynamicFormElements], action_name: str):
        root_len = len(form_elements)
        pages_len = len(
            [f for f in form_elements if f.TYPE == ActionFieldType.LAYOUT and f._component == "Page"],  # type: ignore
        )
        if pages_len > 0 and pages_len != root_len:
            raise DatasourceToolkitException(
                f"You cannot mix pages and other form elements in smart action '{action_name}' form"
            )

    def _validate_id_uniqueness(self, form_elements: List[DynamicFormElements], used=None):
        if used is None:
            used = set()

        for element in form_elements:
            if element.TYPE == ActionFieldType.LAYOUT:
                element = cast(DynamicLayoutElements, element)
                if element._component == "Row":
                    self._validate_id_uniqueness(element._row_subfields, used)  # type: ignore
                elif element._component == "Page":
                    self._validate_id_uniqueness(element._page_elements, used)  # type: ignore
            else:
                element = cast(BaseDynamicField, element)
                if element.id in used:
                    raise DatasourceToolkitException(
                        f"All field must have different 'id'. Conflict come from field '{element.id}'"
                    )
                used.add(element.id)

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
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[ActionFormElement]:
        if meta is None:
            meta = {}
        action = self._actions.get(name)
        if not action:
            return await super().get_form(caller, name, data, filter_, meta)  # type: ignore
        elif not action.get("form"):
            return []

        form_values = data or {}
        used: Set[str] = set()
        context = self._get_context(caller, action, form_values, filter_, used, meta.get("changed_field"))
        form_fields: List[DynamicFormElements] = cast(
            List[DynamicFormElements], [field for field in action.get("form", [])]
        )
        if meta.get("search_field"):
            # in the case of a search hook,
            # we don't want to rebuild all the fields. only the one searched
            form_fields = [self._search_field_in_form(meta["search_field"], form_fields)]  # type: ignore

        form_values = await self._build_form_values(context, form_fields, form_values)
        context.form_values.update(form_values)
        action_fields = await self._build_fields(
            context, form_fields, form_values, meta.get("search_values", {}).get(meta.get("search_field"))
        )

        self._set_watch_changes_attr(action_fields, context)
        return action_fields

    def _search_field_in_form(
        self, field_id: str, form_elements: List[BaseActionFormElement]
    ) -> ActionField:  # type: ignore
        for field in form_elements:
            if isinstance(field, BaseDynamicField):
                if field.id == field_id:
                    return field  # type: ignore
            elif isinstance(field, DynamicLayoutElements):
                if field._component == "Row":
                    return self._search_field_in_form(field_id, field._row_subfields)  # type: ignore
                if field._component == "Page":
                    return self._search_field_in_form(field_id, field._page_elements)  # type: ignore

    def _set_watch_changes_attr(
        self, form_elements: List[Union[ActionLayoutElement, ActionField]], context: ActionContext
    ):
        for element in form_elements:
            if element["type"] not in [ActionFieldType.LAYOUT, "Layout"]:
                element["watch_changes"] = element["id"] in context.form_values.used_keys  # type:ignore
            elif element["component"] == "Row":  # type:ignore
                self._set_watch_changes_attr(element["fields"], context)  # type:ignore
            elif element["component"] == "Page":  # type:ignore
                self._set_watch_changes_attr(element["elements"], context)  # type:ignore

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        actions_schema = {}
        for name, action in self._actions.items():
            dynamics: List[bool] = []
            for field in action.get("form", []):
                dynamics.append(field.is_dynamic)  # type:ignore

            actions_schema[name] = Action(
                scope=ActionsScope(action["scope"]),
                generate_file=action.get("generate_file", False),
                static_form=not any(dynamics),
                description=action.get("description"),
                submit_button_label=action.get("submit_button_label"),
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
        }[ActionsScope(action["scope"])](cast(Collection, self), caller, form_values, filter_, used, changed_field)

    async def _build_form_values(
        self, context: ActionContext, fields: List[DynamicFormElements], data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if data is None:
            form_values: Dict[str, Any] = {}
        else:
            form_values: Dict[str, Any] = {**data}

        for field in fields:
            if not isinstance(field, DynamicLayoutElements):
                form_values[field.id] = form_values.get(field.id, await field.default_value(context))
            elif isinstance(field, DynamicLayoutElements):
                if field._component == "Page":
                    form_values.update(
                        await self._build_form_values(context, field._page_elements, data),  # type: ignore
                    )
                elif field._component == "Row":
                    form_values.update(
                        await self._build_form_values(context, field._row_subfields, data),  # type: ignore
                    )

        return form_values

    async def _build_fields(
        self,
        context: ActionContext,
        fields: List[DynamicFormElements],
        form_values: RecordsDataAlias,
        search_value: Optional[str] = None,
    ) -> List[Union[ActionLayoutElement, ActionField]]:
        action_fields: List[Union[ActionLayoutElement, ActionField]] = []
        for field in fields:
            if await field.if_(context):
                value = form_values if isinstance(field, DynamicLayoutElements) else form_values.get(field.id)
                action_field = await field.to_action_field(context, value, search_value)  # type:ignore
                if action_field is not None:
                    action_fields.append(action_field)
        return action_fields
