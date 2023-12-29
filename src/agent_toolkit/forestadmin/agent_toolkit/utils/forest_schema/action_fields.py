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

    @staticmethod
    def is_text_input_list_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "TextInputList"

    @staticmethod
    def is_text_area_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "TextArea"

    @staticmethod
    def is_rich_text_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "RichText"

    @staticmethod
    def is_address_autocomplete_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "AddressAutocomplete"

    @staticmethod
    def is_number_input_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "NumberInput"

    @staticmethod
    def is_currency_input_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "CurrencyInput"

    @staticmethod
    def is_number_input_list_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "NumberInputList"

    @staticmethod
    def is_json_editor_field(field: ActionField) -> bool:
        return field is not None and field.get("widget", "") == "JsonEditor"
