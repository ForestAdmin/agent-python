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
