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


class TestGeneratorActionFieldWidgetRichText(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "RichText",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "rich text",
                "parameters": {"placeholder": None},
            },
        )


class TestGeneratorActionFieldWidgetAddressAutocomplete(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING,
                "label": "Label",
                "watch_changes": False,
                "widget": "AddressAutocomplete",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "address editor",
                "parameters": {"placeholder": None},
            },
        )


class TestGeneratorActionFieldWidgetTextInputList(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "TextInputList",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "input array",
                "parameters": {
                    "placeholder": None,
                    "allowDuplicate": False,
                    "allowEmptyValue": False,
                    "enableReorder": True,
                },
            },
        )


class TestGeneratorActionFieldWidgetNumberInput(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.NUMBER,
                "label": "Label",
                "watch_changes": False,
                "widget": "NumberInput",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "number input",
                "parameters": {
                    "placeholder": None,
                    "min": None,
                    "max": None,
                    "step": None,
                },
            },
        )


class TestGeneratorActionFieldWidgetNumberInputList(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "NumberInputList",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "input array",
                "parameters": {
                    "placeholder": None,
                    "min": None,
                    "max": None,
                    "step": None,
                    "allowDuplicate": False,
                    "enableReorder": True,
                },
            },
        )


class TestGeneratorActionFieldWidgetCurrencyInput(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "CurrencyInput",
                "currency": "usd",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "price editor",
                "parameters": {
                    "min": None,
                    "max": None,
                    "step": None,
                    "placeholder": None,
                    "currency": "usd",
                    "base": "Unit",
                },
            },
        )


class TestGeneratorActionFieldWidgetJsonEditor(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.NUMBER_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "JsonEditor",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "json code editor",
                "parameters": {},
            },
        )


class TestGeneratorActionFieldWidgetFilePicker(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.FILE,
                "label": "Label",
                "watch_changes": False,
                "widget": "FilePicker",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "file picker",
                "parameters": {
                    "prefix": None,
                    "filesExtensions": None,
                    "filesCountLimit": None,
                    "filesSizeLimit": None,
                },
            },
        )


class TestGeneratorActionFieldWidgetDatePicker(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.DATE,
                "label": "Label",
                "watch_changes": False,
                "widget": "DatePicker",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "date editor",
                "parameters": {
                    "placeholder": None,
                    "format": None,
                    "minDate": None,
                    "maxDate": None,
                },
            },
        )


class TestGeneratorActionFieldWidgetTimePicker(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.TIME,
                "label": "Label",
                "watch_changes": False,
                "widget": "TimePicker",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "time editor",
                "parameters": {},
            },
        )


class TestGeneratorActionFieldWidgetCheckbox(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.BOOLEAN,
                "label": "Label",
                "watch_changes": False,
                "widget": "Checkbox",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "boolean editor",
                "parameters": {},
            },
        )


class TestGeneratorActionFieldWidgetRadioGroup(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "RadioGroup",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "radio button",
                "parameters": {"static": {"options": []}},
            },
        )


class TestGeneratorActionFieldWidgetCheckboxGroup(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "CheckboxGroup",
            }
        )
        self.assertEqual(
            result,
            {"name": "checkboxes", "parameters": {"static": {"options": []}}},
        )


class TestGeneratorActionFieldWidgetDropdown(TestCase):
    def test_build_widget_option_should_return_valid_widget_edit_with_default_values(self):
        result = GeneratorActionFieldWidget.build_widget_options(
            {
                "type": ActionFieldType.STRING_LIST,
                "label": "Label",
                "watch_changes": False,
                "widget": "Dropdown",
            }
        )
        self.assertEqual(
            result,
            {
                "name": "dropdown",
                "parameters": {
                    "placeholder": None,
                    "static": {"options": []},
                    "searchType": None,
                    "isSearchable": False,
                },
            },
        )
