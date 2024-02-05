import asyncio
from unittest import TestCase
from unittest.mock import Mock

from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class TestSchemaActionGenerator(TestCase):
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
                "baseUrl": None,
                "endpoint": "/forest/_actions/Book/0/send email",
                "httpMethod": "POST",
                "redirect": None,
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
                "baseUrl": None,
                "endpoint": "/forest/_actions/Book/0/send email",
                "httpMethod": "POST",
                "redirect": None,
                "download": False,
                "fields": [
                    {
                        "field": "label",
                        "value": None,
                        "defaultValue": None,
                        "description": "email",
                        "enums": None,
                        "hook": None,
                        "isReadOnly": False,
                        "isRequired": True,
                        "reference": None,
                        "type": "String",
                        "widget": None,
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
                "value": None,
                "defaultValue": None,
                "description": "email",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": "String",
                "widget": None,
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
                        "label": "avatar",
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
                "value": None,
                "defaultValue": None,
                "description": "choose an author",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": "Author.primary_id",
                "type": "Uuid",
                "widget": None,
                "widgetEdit": None,
            },
        )

        self.assertEqual(
            result["fields"][1],
            {
                "field": "avatar",
                "value": None,
                "defaultValue": None,
                "description": "choose an avatar",
                "enums": None,
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": "File",
                "widget": None,
                "widgetEdit": None,
            },
        )

        self.assertEqual(
            result["fields"][2],
            {
                "field": "avatar",
                "value": [],
                "defaultValue": None,
                "description": "Choose None, Male, Female or Both",
                "enums": ["Male", "Female"],
                "hook": None,
                "isReadOnly": False,
                "isRequired": True,
                "reference": None,
                "type": ["Enum"],
                "widget": None,
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
        self.assertIsNone(result["fields"][0]["widget"])
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
