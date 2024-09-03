from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainLayoutPageConfiguration,
    PlainLayoutRowConfiguration,
    PlainLayoutSeparatorConfiguration,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionLayoutItem
from typing_extensions import TypeGuard


class ActionLayout:
    @staticmethod
    def is_row_field(field: ActionLayoutItem) -> TypeGuard[PlainLayoutRowConfiguration]:
        return field is not None and field.get("widget", "") == "Row"

    @staticmethod
    def is_separator_field(field: ActionLayoutItem) -> TypeGuard[PlainLayoutSeparatorConfiguration]:
        return field is not None and field.get("widget", "") == "Separator"

    @staticmethod
    def is_page_field(field: ActionLayoutItem) -> TypeGuard[PlainLayoutPageConfiguration]:
        return field is not None and field.get("widget", "") == "Page"
