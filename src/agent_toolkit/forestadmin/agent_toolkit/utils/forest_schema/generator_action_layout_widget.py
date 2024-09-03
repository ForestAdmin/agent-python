from typing import Union

from forestadmin.agent_toolkit.utils.forest_schema.action_layout import ActionLayout
from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerActionFieldPageOptions,
    ForestServerActionFieldRowOptions,
    ForestServerActionFieldSeparatorOptions,
    LayoutWidgetConfiguration,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainLayoutPageConfiguration,
    PlainLayoutRowConfiguration,
    PlainLayoutSeparatorConfiguration,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionLayoutItem


class GeneratorActionLayoutWidget:

    @staticmethod
    def build_widget_options(field: ActionLayoutItem) -> Union[LayoutWidgetConfiguration, None]:
        if_return_mapping = {
            ActionLayout.is_row_field: GeneratorActionLayoutWidget.build_row_widget_edit,
            ActionLayout.is_separator_field: GeneratorActionLayoutWidget.build_separator_widget_edit,
            ActionLayout.is_page_field: GeneratorActionLayoutWidget.build_page_widget_edit,
        }
        for if_fn, return_fn in if_return_mapping.items():
            if if_fn(field):
                return return_fn(field)

    @staticmethod
    def build_row_widget_edit(field: PlainLayoutRowConfiguration) -> ForestServerActionFieldRowOptions:
        return {
            "name": "row",
            "parameters": {
                "fields": field["fields"],
                # "size": [field.get("size", [None, None])[0], field.get("size", [None, None])[1]],
            },
        }

    @staticmethod
    def build_separator_widget_edit(
        field: PlainLayoutSeparatorConfiguration,
    ) -> ForestServerActionFieldSeparatorOptions:
        return {
            "name": "separator",
        }

    @staticmethod
    def build_page_widget_edit(field: PlainLayoutPageConfiguration) -> ForestServerActionFieldPageOptions:
        return {
            "name": "page",
            "parameters": {
                "previousButtonLabel": field.get("previous_button_label"),
                "nextButtonLabel": field.get("next_button_label"),
                "elements": field.get("elements", []),  # type: ignore
            },
        }
