from unittest import TestCase

from forestadmin.agent_toolkit.utils.forest_schema.generator_action_field_widget import GeneratorActionFieldWidget
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType


class TestGeneratorActionFieldWidget(TestCase):
    def test_build_widget_option_should_return_none_when_field_has_no_widget(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
            }
        )
        self.assertIsNone(result)

    def test_build_widget_option_should_return_none_when_field_is_collection(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.COLLECTION,
                "label": "Label",
                "watch_changes": False,
            }
        )
        self.assertIsNone(result)

    def test_build_widget_option_should_return_none_when_field_is_enum(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.ENUM,
                "label": "Label",
                "watch_changes": False,
            }
        )
        self.assertIsNone(result)

    def test_build_widget_option_should_return_none_when_field_is_enum_list(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.ENUM_LIST,
                "label": "Label",
                "watch_changes": False,
            }
        )
        self.assertIsNone(result)


class TestGeneratorActionFieldWidgetColorPicker(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "ColorPicker",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "color editor",
                "parameters": {
                    "enableOpacity": False,
                    "placeholder": None,
                    "quickPalette": None,
                },
            },
        )


class TestGeneratorActionFieldWidgetTextInput(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextInput",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "text editor",
                "parameters": {
                    "placeholder": None,
                },
            },
        )


class TestGeneratorActionFieldWidgetTextArea(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextArea",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "text area editor",
                "parameters": {"placeholder": None, "rows": None},
            },
        )
