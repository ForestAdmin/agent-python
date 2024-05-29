from datetime import date
from typing import Literal, Union

from forestadmin.agent_toolkit.utils.forest_schema.action_fields import ActionFields
from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerActionFieldAddressAutocompleteEditorOptions,
    ForestServerActionFieldCheckboxGroupOptions,
    ForestServerActionFieldCheckboxOptions,
    ForestServerActionFieldColorPickerOptions,
    ForestServerActionFieldCurrencyInputEditorOptions,
    ForestServerActionFieldDatePickerOptions,
    ForestServerActionFieldDropdownOptions,
    ForestServerActionFieldFilePickerEditorOptions,
    ForestServerActionFieldJsonEditorEditorOptions,
    ForestServerActionFieldNumberInputEditorOptions,
    ForestServerActionFieldNumberInputListEditorOptions,
    ForestServerActionFieldRadioGroupOptions,
    ForestServerActionFieldRichTextEditorOptions,
    ForestServerActionFieldTextAreaEditorOptions,
    ForestServerActionFieldTextEditorOptions,
    ForestServerActionFieldTextListEditorOptions,
    ForestServerActionFieldTimePickerOptions,
    ForestServerActionFieldUserDropdownOptions,
    WidgetEditConfiguration,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainBooleanDynamicFieldCheckboxWidget,
    PlainDateDynamicFieldDatePickerWidget,
    PlainDateOnlyDynamicFieldDatePickerWidget,
    PlainFileDynamicFieldFilePickerWidget,
    PlainFileListDynamicFieldFilePickerWidget,
    PlainJsonDynamicFieldJsonEditorWidget,
    PlainListNumberDynamicFieldNumberInputListWidget,
    PlainNumberDynamicFieldCurrencyInputWidget,
    PlainNumberDynamicFieldNumberInputWidget,
    PlainStringDynamicFieldAddressAutocompleteWidget,
    PlainStringDynamicFieldColorWidget,
    PlainStringDynamicFieldRichTextWidget,
    PlainStringDynamicFieldTextAreaWidget,
    PlainStringDynamicFieldTextInputWidget,
    PlainStringDynamicFieldUserDropdownFieldConfiguration,
    PlainStringListDynamicFieldTextInputListWidget,
    PlainStringListDynamicFieldUserDropdownFieldConfiguration,
    PlainTimeDynamicFieldTimePickerWidget,
)
from forestadmin.datasource_toolkit.decorators.action.types.widgets import (
    CheckboxesFieldConfiguration,
    DropdownDynamicSearchFieldConfiguration,
    RadioButtonFieldConfiguration,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType


class GeneratorActionFieldWidget:
    NO_WIDGET_FOR_FIELD_TYPES = (ActionFieldType.COLLECTION, ActionFieldType.ENUM, ActionFieldType.ENUM_LIST)

    @staticmethod
    def build_widget_options(field: ActionField) -> Union[WidgetEditConfiguration, None]:  # noqa: C901
        if not ActionFields.has_widget(field) or field["type"] in GeneratorActionFieldWidget.NO_WIDGET_FOR_FIELD_TYPES:
            return None

        if_return_mapping = {
            ActionFields.is_color_picker_field: GeneratorActionFieldWidget.build_color_picker_widget_edit,
            ActionFields.is_text_input_field: GeneratorActionFieldWidget.build_text_input_widget_edit,
            ActionFields.is_text_input_list_field: GeneratorActionFieldWidget.build_text_input_list_widget_edit,
            ActionFields.is_text_area_field: GeneratorActionFieldWidget.build_text_area_widget_edit,
            ActionFields.is_rich_text_field: GeneratorActionFieldWidget.build_rich_text_widget_edit,
            ActionFields.is_address_autocomplete_field: (
                GeneratorActionFieldWidget.build_address_autocomplete_widget_edit
            ),
            ActionFields.is_number_input_field: GeneratorActionFieldWidget.build_number_input_widget_edit,
            ActionFields.is_currency_input_field: GeneratorActionFieldWidget.build_currency_input_widget_edit,
            ActionFields.is_number_input_list_field: GeneratorActionFieldWidget.build_number_input_list_widget_edit,
            ActionFields.is_json_editor_field: GeneratorActionFieldWidget.build_json_editor_widget_edit,
            ActionFields.is_file_picker_field: GeneratorActionFieldWidget.build_file_picker_widget_edit,
            ActionFields.is_date_picker_field: GeneratorActionFieldWidget.build_date_picker_widget_edit,
            ActionFields.is_time_picker_field: GeneratorActionFieldWidget.build_time_picker_widget_edit,
            ActionFields.is_checkbox_field: GeneratorActionFieldWidget.build_checkbox_widget_edit,
            ActionFields.is_radio_group_field: GeneratorActionFieldWidget.build_radio_group_widget_edit,
            ActionFields.is_checkbox_group_field: GeneratorActionFieldWidget.build_checkbox_group_widget_edit,
            ActionFields.is_dropdown_field: GeneratorActionFieldWidget.build_dropdown_widget_edit,
            ActionFields.is_user_dropdown_field: GeneratorActionFieldWidget.build_user_dropdown_widget_edit,
        }
        for if_fn, return_fn in if_return_mapping.items():
            if if_fn(field):
                return return_fn(field)

    @staticmethod
    def build_color_picker_widget_edit(
        field: PlainStringDynamicFieldColorWidget,
    ) -> ForestServerActionFieldColorPickerOptions:
        return {
            "name": "color editor",
            "parameters": {
                "enableOpacity": field.get("enable_opacity", False),
                "placeholder": field.get("placeholder"),
                "quickPalette": field.get("quick_palette", []) if len(field.get("quick_palette", [])) > 0 else None,
            },
        }

    @staticmethod
    def build_text_input_widget_edit(
        field: PlainStringDynamicFieldTextInputWidget,
    ) -> ForestServerActionFieldTextEditorOptions:
        return {
            "name": "text editor",
            "parameters": {
                "placeholder": field.get("placeholder"),
            },
        }

    @staticmethod
    def build_text_input_list_widget_edit(
        field: PlainStringListDynamicFieldTextInputListWidget,
    ) -> ForestServerActionFieldTextListEditorOptions:
        return {
            "name": "input array",
            "parameters": {
                "placeholder": field.get("placeholder"),
                "allowDuplicate": field.get("allow_duplicates", False),
                "allowEmptyValue": field.get("allow_empty_values", False),
                "enableReorder": field.get("enable_reorder", True),
            },
        }

    @staticmethod
    def build_text_area_widget_edit(
        field: PlainStringDynamicFieldTextAreaWidget,
    ) -> ForestServerActionFieldTextAreaEditorOptions:
        return {
            "name": "text area editor",
            "parameters": {
                "placeholder": field.get("placeholder"),
                "rows": int(field["rows"]) if field.get("rows") is not None else None,
            },
        }

    @staticmethod
    def build_rich_text_widget_edit(
        field: PlainStringDynamicFieldRichTextWidget,
    ) -> ForestServerActionFieldRichTextEditorOptions:
        return {
            "name": "rich text",
            "parameters": {
                "placeholder": field.get("placeholder"),
            },
        }

    @staticmethod
    def build_address_autocomplete_widget_edit(
        field: PlainStringDynamicFieldAddressAutocompleteWidget,
    ) -> ForestServerActionFieldAddressAutocompleteEditorOptions:
        return {
            "name": "address editor",
            "parameters": {
                "placeholder": field.get("placeholder"),
            },
        }

    @staticmethod
    def build_number_input_widget_edit(
        field: PlainNumberDynamicFieldNumberInputWidget,
    ) -> ForestServerActionFieldNumberInputEditorOptions:
        return {
            "name": "number input",
            "parameters": {
                "placeholder": field.get("placeholder"),
                "min": field.get("min"),  #  type:ignore
                "max": field.get("max"),  #  type:ignore
                "step": field.get("step"),  #  type:ignore
            },
        }

    @staticmethod
    def build_currency_input_widget_edit(
        field: PlainNumberDynamicFieldCurrencyInputWidget,
    ) -> ForestServerActionFieldCurrencyInputEditorOptions:
        return {
            "name": "price editor",
            "parameters": {
                "placeholder": field.get("placeholder"),
                "min": field.get("min"),  #  type:ignore
                "max": field.get("max"),
                "step": field.get("step"),
                "currency": (
                    field["currency"]
                    if isinstance(field.get("currency"), str) and len(field["currency"]) == 3
                    else None
                ),
                "base": GeneratorActionFieldWidget._map_currency_base(field.get("base")),
            },
        }

    @staticmethod
    def _map_currency_base(base: str) -> Literal["Unit", "Cent"]:
        try:
            if base.lower() in ["cent", "cents"]:
                return "Cent"
            elif base.lower() in ["unit", "units"]:
                return "Unit"
        except Exception:
            pass
            # return "Unit" as default value
        return "Unit"

    @staticmethod
    def build_number_input_list_widget_edit(
        field: PlainListNumberDynamicFieldNumberInputListWidget,
    ) -> ForestServerActionFieldNumberInputListEditorOptions:
        return {
            "name": "input array",
            "parameters": {
                "placeholder": field.get("placeholder"),
                "min": field.get("min"),  # type: ignore
                "max": field.get("max"),
                "step": field.get("step"),
                "allowDuplicate": field.get("allow_duplicates", False),
                "enableReorder": field.get("enable_reorder", True),
            },
        }

    @staticmethod
    def build_json_editor_widget_edit(
        field: PlainJsonDynamicFieldJsonEditorWidget,
    ) -> ForestServerActionFieldJsonEditorEditorOptions:
        return {"name": "json code editor", "parameters": {}}

    @staticmethod
    def build_file_picker_widget_edit(
        field: Union[PlainFileDynamicFieldFilePickerWidget, PlainFileListDynamicFieldFilePickerWidget],
    ) -> ForestServerActionFieldFilePickerEditorOptions:
        return {
            "name": "file picker",
            "parameters": {
                "prefix": None,  # type:ignore
                "filesExtensions": field.get("extensions", None),
                "filesCountLimit": field.get("max_count"),
                "filesSizeLimit": field.get("max_size_mb"),
            },
        }

    @staticmethod
    def build_date_picker_widget_edit(
        field: Union[PlainDateDynamicFieldDatePickerWidget, PlainDateOnlyDynamicFieldDatePickerWidget],
    ) -> ForestServerActionFieldDatePickerOptions:
        return {
            "name": "date editor",
            "parameters": {
                "format": field.get("format"),  # type:ignore
                "placeholder": field.get("placeholder"),
                "minDate": field["min"].isoformat() if isinstance(field.get("min"), date) else None,
                "maxDate": field["max"].isoformat() if isinstance(field.get("max"), date) else None,
            },
        }

    @staticmethod
    def build_time_picker_widget_edit(
        field: PlainTimeDynamicFieldTimePickerWidget,
    ) -> ForestServerActionFieldTimePickerOptions:
        return {
            "name": "time editor",
            "parameters": {},
        }

    @staticmethod
    def build_checkbox_widget_edit(
        field: PlainBooleanDynamicFieldCheckboxWidget,
    ) -> ForestServerActionFieldCheckboxOptions:
        return {
            "name": "boolean editor",
            "parameters": {},
        }

    @staticmethod
    def build_radio_group_widget_edit(
        field: Union[
            RadioButtonFieldConfiguration[str], RadioButtonFieldConfiguration[int], RadioButtonFieldConfiguration[float]
        ],
    ) -> Union[
        ForestServerActionFieldRadioGroupOptions[int],
        ForestServerActionFieldRadioGroupOptions[float],
        ForestServerActionFieldRadioGroupOptions[str],
    ]:
        return {
            "name": "radio button",
            "parameters": {
                "static": {  # type:ignore
                    "options": field.get("options", []),
                },
            },
        }

    @staticmethod
    def build_checkbox_group_widget_edit(
        field: Union[
            CheckboxesFieldConfiguration[str], CheckboxesFieldConfiguration[int], CheckboxesFieldConfiguration[float]
        ],
    ) -> Union[
        ForestServerActionFieldCheckboxGroupOptions[int],
        ForestServerActionFieldCheckboxGroupOptions[float],
        ForestServerActionFieldCheckboxGroupOptions[str],
    ]:
        return {
            "name": "checkboxes",
            "parameters": {
                "static": {  # type:ignore
                    "options": field.get("options", []),
                },
            },
        }

    @staticmethod
    def build_dropdown_widget_edit(
        field: Union[
            DropdownDynamicSearchFieldConfiguration[str],
            DropdownDynamicSearchFieldConfiguration[int],
            DropdownDynamicSearchFieldConfiguration[float],
        ],
    ) -> Union[
        ForestServerActionFieldDropdownOptions[int],
        ForestServerActionFieldDropdownOptions[float],
        ForestServerActionFieldDropdownOptions[str],
    ]:
        return {
            "name": "dropdown",
            "parameters": {
                "searchType": "dynamic" if field.get("search", "") == "dynamic" else None,
                "isSearchable": field.get("search") in ["static", "dynamic"],
                "placeholder": field.get("placeholder"),
                "static": {"options": field.get("options", [])},
            },
        }

    @staticmethod
    def build_user_dropdown_widget_edit(
        field: Union[
            PlainStringListDynamicFieldUserDropdownFieldConfiguration,
            PlainStringDynamicFieldUserDropdownFieldConfiguration,
        ],
    ) -> ForestServerActionFieldUserDropdownOptions:
        return {
            "name": "assignee editor",
            "parameters": {
                "placeholder": field.get("placeholder"),
            },
        }
