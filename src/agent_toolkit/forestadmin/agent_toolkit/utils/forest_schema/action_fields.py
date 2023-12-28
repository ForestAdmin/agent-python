from forestadmin.datasource_toolkit.interfaces.actions import ActionField


class ActionFields:
    @staticmethod
    def has_widget(field: ActionField):
        return field and field.get("widget") is not None

    @staticmethod
    def is_color_picker_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "ColorPicker"

    @staticmethod
    def is_text_input_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "TextInput"
