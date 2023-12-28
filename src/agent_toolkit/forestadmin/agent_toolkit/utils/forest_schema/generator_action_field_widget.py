from typing import Union

from forestadmin.agent_toolkit.utils.forest_schema.action_fields import ActionFields
from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerActionFieldColorPickerOptions,
    ForestServerActionFieldTextEditorOptions,
    WidgetEditConfiguration,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainStringDynamicFieldColorWidget,
    PlainStringDynamicFieldTextInputWidget,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType


class GeneratorActionFieldWidget:
    NO_WIDGET_FOR_FIELD_TYPES = (ActionFieldType.COLLECTION, ActionFieldType.ENUM, ActionFieldType.ENUM_LIST)

    @staticmethod
    def build_widget_options(field: ActionField) -> Union[WidgetEditConfiguration, None]:
        if not ActionFields.has_widget(field) or field["type"] in GeneratorActionFieldWidget.NO_WIDGET_FOR_FIELD_TYPES:
            return None

        if ActionFields.is_color_picker_field(field):
            return GeneratorActionFieldWidget.build_color_picker_widget_edit(field)

        if ActionFields.is_text_input_field(field):
            return GeneratorActionFieldWidget.build_text_input_widget_edit(field)

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
