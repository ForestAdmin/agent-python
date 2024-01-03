from unittest import TestCase

from forestadmin.agent_toolkit.utils.forest_schema.action_fields import ActionFields
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType


class TestActionFields(TestCase):
    def test_has_widget_should_return_true_when_it_has_widget(self):
        result = ActionFields.has_widget(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "ANY",
            }
        )
        self.assertTrue(result)

    def test_has_widget_should_return_false_when_it_has_no_widget(self):
        result = ActionFields.has_widget(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
            }
        )
        self.assertFalse(result)


class TestIsColorPicker(TestCase):
    def test_should_return_true_when_its_color_picker(self):
        result = ActionFields.is_color_picker_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "ColorPicker",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_color_picker(self):
        result = ActionFields.is_color_picker_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_color_picker_field(None)
        self.assertFalse(result)


class TestIsTextField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_text_input_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextInput",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_text_input(self):
        result = ActionFields.is_text_input_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_text_input_field(None)
        self.assertFalse(result)


class TestIsTextAreaField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_text_area_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextArea",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_text_area(self):
        result = ActionFields.is_text_area_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_text_area_field(None)
        self.assertFalse(result)


class TestIsRichTextField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_rich_text_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "RichText",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_rich_text_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_rich_text_field(None)
        self.assertFalse(result)


class TestIsAddressAutocompleteField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_address_autocomplete_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "AddressAutocomplete",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_address_autocomplete_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_address_autocomplete_field(None)
        self.assertFalse(result)


class TestIsTextInputListField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_text_input_list_field(
            {
                "type": ActionFieldType.STRING_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextInputList",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_text_input_list_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_text_input_list_field(None)
        self.assertFalse(result)


class TestIsNumberInputField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_number_input_field(
            {
                "type": ActionFieldType.NUMBER,
                "label": "Label",
                "watch_changes": False,
                "widget": "NumberInput",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_number_input_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_number_input_field(None)
        self.assertFalse(result)


class TestIsNumberInputListField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_number_input_list_field(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "NumberInputList",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_number_input_list_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_number_input_list_field(None)
        self.assertFalse(result)


class TestIsCurrencyInputField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_currency_input_field(
            {
                "type": ActionFieldType.NUMBER,
                "label": "Label",
                "watch_changes": False,
                "widget": "CurrencyInput",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_currency_input_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_currency_input_field(None)
        self.assertFalse(result)


class TestIsJsonEditorField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_json_editor_field(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "JsonEditor",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_json_editor_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_json_editor_field(None)
        self.assertFalse(result)


class TestIsFilePickerField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_file_picker_field(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "FilePicker",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_file_picker_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_file_picker_field(None)
        self.assertFalse(result)


class TestIsDatePickerField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_date_picker_field(
            {
                "type": ActionFieldType.DATE,
                "label": "Label",
                "watch_changes": False,
                "widget": "DatePicker",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_date_picker_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_date_picker_field(None)
        self.assertFalse(result)


class TestIsTimePickerField(TestCase):
    def test_should_return_true_when_its_text_input(self):
        result = ActionFields.is_time_picker_field(
            {
                "type": ActionFieldType.TIME,
                "label": "Label",
                "watch_changes": False,
                "widget": "TimePicker",
            }
        )
        self.assertTrue(result)

    def test_should_return_false_when_its_not_rich_text(self):
        result = ActionFields.is_time_picker_field(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertFalse(result)

    def test_should_return_false_when_field_is_none(self):
        result = ActionFields.is_time_picker_field(None)
        self.assertFalse(result)
