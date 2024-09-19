import asyncio
from unittest import TestCase, skip
from unittest.mock import Mock

from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class BaseTestSchemaActionGenerator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.book_collection = Collection("Book", cls.datasource)
        cls.datasource.add_collection(cls.book_collection)
        cls.author_collection = Collection("Author", cls.datasource)
        cls.author_collection.add_fields(
            {
                "primary_id": {
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.UUID,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.UUID]),
                }
            }
        )
        cls.datasource.add_collection(cls.author_collection)

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, ActionCollectionDecorator)
        self.book_collection_action = self.datasource_decorator.get_collection("Book")


class TestSchemaActionGenerator(BaseTestSchemaActionGenerator):
    def test_should_work_without_form(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result,
            {
                "id": "Book-0-send email",
                "name": "Send email",
                "type": "single",
                "endpoint": "/forest/_actions/Book/0/send email",
                "download": False,
                "fields": [],
                "hooks": {"load": False, "change": ["changeHook"]},
            },
        )

    def test_should_work_without_hook(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {
                        "label": "label",
                        "description": "email",
                        "type": ActionFieldType.STRING,
                        "is_required": True,
                        "is_read_only": False,
                        "value": "",
                    }
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result,
            {
                "id": "Book-0-send email",
                "name": "Send email",
                "type": "single",
                "endpoint": "/forest/_actions/Book/0/send email",
                "download": False,
                "fields": [
                    {
                        "field": "label",
                        "label": "label",
                        "value": None,
                        "defaultValue": None,
                        "description": "email",
                        "enums": None,
                        "hook": None,
                        "isReadOnly": False,
                        "isRequired": True,
                        "reference": None,
                        "type": "String",
                        "widgetEdit": None,
                    }
                ],
                "hooks": {"load": False, "change": ["changeHook"]},
            },
        )

    def test_should_work_with_change_hook(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {
                        "label": "label",
                        "description": "email",
                        "type": ActionFieldType.STRING,
                        "is_required": True,
                        "is_read_only": False,
                        "value": "",
                    }
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result["fields"][0],
            {
                "field": "label",
                "label": "label",
                "value": None,
                "defaultValue": None,
                "description": "email",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": "String",
                "widgetEdit": None,
            },
        )

    def test_should_work_with_special_fields(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {
                        "label": "author",
                        "description": "choose an author",
                        "type": ActionFieldType.COLLECTION,
                        "is_required": True,
                        "is_read_only": False,
                        "value": None,
                        "collection_name": "Author",
                    },
                    {
                        "label": "avatar",
                        "description": "choose an avatar",
                        "type": ActionFieldType.FILE,
                        "is_required": True,
                        "is_read_only": False,
                        "value": None,
                    },
                    {
                        "label": "gender",
                        "description": "Choose None, Male, Female or Both",
                        "type": ActionFieldType.ENUM_LIST,
                        "is_required": True,
                        "is_read_only": False,
                        "value": None,
                        "enum_values": ["Male", "Female"],
                    },
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result["fields"][0],
            {
                "field": "author",
                "label": "author",
                "value": None,
                "defaultValue": None,
                "description": "choose an author",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": "Author.primary_id",
                "type": "Uuid",
                "widgetEdit": None,
            },
        )

        self.assertEqual(
            result["fields"][1],
            {
                "field": "avatar",
                "label": "avatar",
                "value": None,
                "defaultValue": None,
                "description": "choose an avatar",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": "File",
                "widgetEdit": None,
            },
        )

        self.assertEqual(
            result["fields"][2],
            {
                "field": "gender",
                "label": "gender",
                "value": [],
                "defaultValue": None,
                "description": "Choose None, Male, Female or Both",
                "enums": ["Male", "Female"],
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": ["Enum"],
                "widgetEdit": None,
            },
        )

    def test_should_set_none_to_widget(self):
        self.book_collection_action.add_action(
            "Update title",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {
                        "label": "label",
                        "description": "email",
                        "type": ActionFieldType.STRING,
                        "is_required": True,
                        "is_read_only": False,
                        "value": "",
                    }
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Update title")
        )
        self.assertIsNone(result["fields"][0]["widgetEdit"])

    def test_should_generate_widget_configuration(self):
        self.book_collection_action.add_action(
            "Update title",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {
                        "label": "color",
                        "description": "color",
                        "type": ActionFieldType.STRING,
                        "is_required": True,
                        "is_read_only": False,
                        "value": "",
                        "widget": "ColorPicker",
                    }
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Update title")
        )
        self.assertEqual(
            result["fields"][0]["widgetEdit"],
            {
                "name": "color editor",
                "parameters": {
                    "enableOpacity": False,
                    "placeholder": None,
                    "quickPalette": None,
                },
            },
        )


class TestSchemaActionGeneratorLayout(BaseTestSchemaActionGenerator):
    @skip("restore it for story#7")
    def test_should_generate_layout_only_if_there_is_layout_elements(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {"type": "String", "label": "firstname"},
                    {"type": "Layout", "component": "Separator"},
                    {"type": "String", "label": "lastname"},
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result["fields"],
            [
                {
                    "field": "firstname",
                    "value": None,
                    "defaultValue": None,
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isReadOnly": False,
                    "isRequired": False,
                    "reference": None,
                    "type": "String",
                    "widgetEdit": None,
                },
                {
                    "field": "lastname",
                    "value": None,
                    "defaultValue": None,
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isReadOnly": False,
                    "isRequired": False,
                    "reference": None,
                    "type": "String",
                    "widgetEdit": None,
                },
            ],
        )
        self.assertEqual(
            result.get("layout"),
            [
                {"component": "input", "fieldId": "firstname"},
                {"component": "separator"},
                {"component": "input", "fieldId": "lastname"},
            ],
        )

    # TODO: remove after story#7
    def test_should_generate_dynamic_form_if_there_is_layout_element(self):
        self.book_collection_action.add_action(
            "Send email",
            {
                "scope": ActionsScope.SINGLE,
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {"type": "String", "label": "firstname"},
                    {"type": "Layout", "component": "Separator"},
                    {"type": "String", "label": "lastname"},
                ],
            },
        )

        result = self.loop.run_until_complete(
            SchemaActionGenerator.build("", self.book_collection_action, "Send email")
        )
        self.assertEqual(
            result["fields"],
            [
                {
                    "field": "Loading...",
                    "label": "Loading...",
                    "type": "String",
                    "isReadOnly": True,
                    "defaultValue": "Form is loading",
                    "value": None,
                    "description": "",
                    "enums": None,
                    "hook": None,
                    "isRequired": False,
                    "reference": None,
                    "widgetEdit": None,
                }
            ],
        )

    def test_field_layout_separator_should_work_fine(self):
        self.book_collection_action.add_action(
            "test_extract",
            {
                "scope": ActionsScope.SINGLE,
                "execute": Mock(),
                "form": [
                    {"type": "String", "label": "firstname"},
                    {"type": "Layout", "component": "Separator"},
                    {"type": "String", "label": "lastname"},
                    {"type": "Layout", "component": "HtmlBlock", "content": "<b>my html</b>"},
                ],
            },
        )

        fields, layout = SchemaActionGenerator.extract_fields_and_layout(
            self.loop.run_until_complete(self.book_collection_action.get_form(None, "test_extract", None))
        )
        self.assertEqual(
            fields,
            [
                {
                    "type": ActionFieldType.STRING,
                    "id": "firstname",
                    "label": "firstname",
                    "description": "",
                    "is_read_only": False,
                    "is_required": False,
                    "value": None,
                    "default_value": None,
                    "collection_name": None,
                    "enum_values": None,
                    "watch_changes": False,
                },
                {
                    "type": ActionFieldType.STRING,
                    "id": "lastname",
                    "label": "lastname",
                    "description": "",
                    "is_read_only": False,
                    "is_required": False,
                    "value": None,
                    "default_value": None,
                    "collection_name": None,
                    "enum_values": None,
                    "watch_changes": False,
                },
            ],
        )
        self.assertEqual(
            layout,
            [
                {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "firstname"},
                {"type": ActionFieldType.LAYOUT, "component": "Separator"},
                {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "lastname"},
                {"type": ActionFieldType.LAYOUT, "component": "HtmlBlock", "content": "<b>my html</b>"},
            ],
        )

    def test_should_correctly_serialize_separator(self):
        result = self.loop.run_until_complete(
            SchemaActionGenerator.build_layout_schema(
                self.datasource, {"type": ActionFieldType.LAYOUT, "component": "Separator"}
            )
        )
        self.assertEqual(result, {"component": "separator"})

    def test_should_correctly_serialize_inputs_reference(self):
        result = self.loop.run_until_complete(
            SchemaActionGenerator.build_layout_schema(
                self.datasource,
                {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "firstname"},
            )
        )
        self.assertEqual(result, {"component": "input", "fieldId": "firstname"})

    def test_should_correctly_serialize_field_htmlBlock(self):
        result = self.loop.run_until_complete(
            SchemaActionGenerator.build_layout_schema(
                self.datasource, {"type": ActionFieldType.LAYOUT, "component": "HtmlBlock", "content": "<b>my html</b>"}
            )
        )
        self.assertEqual(result, {"component": "htmlBlock", "content": "<b>my html</b>"})

    def test_should_fields_and_layout_should_be_correctly_separated(self):
        fields, layout = SchemaActionGenerator.extract_fields_and_layout(
            [
                {
                    "type": ActionFieldType.LAYOUT,
                    "component": "Row",
                    "fields": [
                        {"type": ActionFieldType.STRING, "label": "gender",  "id": "gender", "watch_changes": True},
                        {"type": ActionFieldType.STRING, "label": "gender_other","id": "gender_other", "watch_changes": True},
                    ],
                }
            ],
        )
        self.assertEqual(
            fields,
            [
                {"type": ActionFieldType.STRING, "label": "gender", "id": "gender", "watch_changes": True},
                {"type": ActionFieldType.STRING, "label": "gender_other", "id": "gender_other", "watch_changes": True},
            ],
        )

        self.assertEqual(
            layout,
            [
                {
                    "type": ActionFieldType.LAYOUT,
                    "component": "Row",
                    "fields": [
                        {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "gender"},
                        {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "gender_other"},
                    ],
                }
            ],
        )

    def test_should_correctly_serialize_row_layout_element(self):
        result = self.loop.run_until_complete(
            SchemaActionGenerator.build_layout_schema(
                self.datasource,
                {
                    "type": ActionFieldType.LAYOUT,
                    "component": "Row",
                    "fields": [
                        {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "gender"},
                        {"type": ActionFieldType.LAYOUT, "component": "Input", "fieldId": "gender_other"},
                    ],
                },
            )
        )

        self.assertEqual(
            result,
            {
                "component": "row",
                "fields": [
                    {"component": "input", "fieldId": "gender"},
                    {"component": "input", "fieldId": "gender_other"},
                ],
            },
        )
