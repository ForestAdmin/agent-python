import asyncio
from unittest import TestCase
from unittest.mock import Mock
from uuid import UUID

from forestadmin.agent_toolkit.utils.forest_schema.action_values import (
    ForestValueConverter,
    ForestValueConverterException,
)
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.collections import ActionCollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, File
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, PrimitiveType
from forestadmin.datasource_toolkit.validations.rules import MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE


class BaseTestForestValueConverter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.book_collection = Collection("Book", cls.datasource)
        cls.book_collection.add_fields(
            {
                "primary_id": {
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.UUID,
                    "filter_operators": set(MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE[PrimitiveType.UUID]),
                }
            }
        )
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
        self.book_collection_action: ActionCollectionDecorator = self.datasource_decorator.get_collection(
            "Book"
        )  # type:ignore


class TestForestValueConverterValueToForest(TestCase):
    def test_should_return_value_on_enum_if_correct(self):
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.ENUM,
                    "watch_changes": False,
                    "label": "test_enum",
                    "enum_values": ["1", "2", "3"],
                    "is_required": True,
                },
                "1",
            ),
            "1",
        )
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.ENUM_LIST,
                    "watch_changes": False,
                    "label": "test_enum",
                    "enum_values": ["1", "2", "3"],
                    "is_required": True,
                },
                ["1"],
            ),
            ["1"],
        )

    def test_should_raise_on_enum_if_value_is_not_allowed(self):
        self.assertRaisesRegex(
            ForestValueConverterException,
            r"4 is not in \['1', '2', '3']",
            ForestValueConverter.value_to_forest,
            {"type": ActionFieldType.ENUM, "label": "test_enum", "enum_values": ["1", "2", "3"]},
            "4",
        )

        self.assertRaisesRegex(
            ForestValueConverterException,
            r"4 is not in \['1', '2', '3']",
            ForestValueConverter.value_to_forest,
            {"type": ActionFieldType.ENUM_LIST, "label": "test_enum", "enum_values": ["1", "2", "3"]},
            ["4"],
        )

    def test_should_raise_on_enum_if_no_enum_values(self):
        self.assertRaisesRegex(
            ForestValueConverterException,
            r"4 is not in None",
            ForestValueConverter.value_to_forest,
            {"type": ActionFieldType.ENUM, "watch_changes": False, "label": "test_enum", "enum_values": None},
            "4",
        )

        self.assertRaisesRegex(
            ForestValueConverterException,
            r"4 is not in None",
            ForestValueConverter.value_to_forest,
            {"type": ActionFieldType.ENUM_LIST, "watch_changes": False, "label": "test_enum", "enum_values": None},
            ["4"],
        )

    def test_should_not_raise_on_enum_if_value_is_none(self):
        self.assertIsNone(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.ENUM,
                    "watch_changes": False,
                    "label": "test_enum",
                    "enum_values": ["1", "2", "3"],
                    "is_required": True,
                },
                None,
            )
        )
        self.assertIsNone(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.ENUM_LIST,
                    "watch_changes": False,
                    "label": "test_enum",
                    "enum_values": ["1", "2", "3"],
                    "is_required": True,
                },
                None,
            )
        )

    def test_should_transform_multi_pk_into_composite(self):
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.COLLECTION,
                    "watch_changes": False,
                    "label": "test_enum",
                },
                ["1", "2"],
            ),
            "1|2",
        )

    def test_should_parse_correctly_pks_when_they_are_integer(self):
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.COLLECTION,
                    "watch_changes": False,
                    "label": "test_enum",
                },
                [1],
            ),
            "1",
        )
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.COLLECTION,
                    "watch_changes": False,
                    "label": "test_enum",
                },
                [1, 2],
            ),
            "1|2",
        )

    def test_should_transform_file_into_datauri(self):
        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.FILE,
                    "watch_changes": False,
                    "label": "test_enum",
                },
                File("text/plain", b"abc", "bla.txt"),
            ),
            "data:text/plain;name=bla.txt;base64,YWJj",
        )

        self.assertEqual(
            ForestValueConverter.value_to_forest(
                {
                    "type": ActionFieldType.FILE_LIST,
                    "watch_changes": False,
                    "label": "test_enum",
                },
                [File("text/plain", b"abc", "bla.txt")],
            ),
            ["data:text/plain;name=bla.txt;base64,YWJj"],
        )


class BaseTestForestValueConverterMakeFormValuesFromField(BaseTestForestValueConverter):
    """use during hook, it only create form_values from data the frontend provide"""

    def setUp(self) -> None:
        super().setUp()
        self.book_collection_action.add_action(
            "test",
            {
                "scope": "Single",
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {"type": "Collection", "collection_name": "Author", "label": "collection"},
                    {"type": "File", "label": "file"},
                    {"type": "FileList", "label": "filelist"},
                    {"type": "String", "label": "string"},
                ],
            },
        )

    def test_should_make_form_values_from_fields(self):
        fields = [
            {
                "value": "19226e17-8430-442b-91a9-2ab96a6997a5",
                "field": "collection",
                "type": ActionFieldType.COLLECTION,
                "reference": "Author.primary_id",
                "isRequired": False,
            },
            {
                "value": "bla bla",
                "field": "string",
                "type": ActionFieldType.STRING,
                "reference": None,
                "isRequired": False,
            },
        ]
        form_values = ForestValueConverter.make_form_data_from_fields(self.datasource, fields)
        self.assertEqual(
            form_values, {"collection": [UUID("19226e17-8430-442b-91a9-2ab96a6997a5")], "string": "bla bla"}
        )

    def test_should_parse_uri_from_file(self):
        fields = [
            {
                "value": "data:text/plain;name=bla.txt;base64,YWJj",
                "field": "file",
                "reference": None,
                "type": ActionFieldType.FILE,
                "isRequired": False,
            },
            {
                "value": ["data:text/plain;name=bla.txt;base64,YWJj"],
                "field": "filelist",
                "reference": None,
                "isRequired": False,
                "type": ActionFieldType.FILE_LIST,
            },
            {
                "value": ["data:text/plain;name=bla.txt;base64,YWJj"],
                "field": "filelist_2",
                "reference": None,
                "isRequired": False,
                "type": [ActionFieldType.FILE],
            },
        ]
        form_values = ForestValueConverter.make_form_data_from_fields(self.datasource, fields)
        self.assertEqual(
            form_values,
            {
                "file": File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None),
                "filelist": [File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None)],
                "filelist_2": [File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None)],
            },
        )


class TestForestValueConverterMakeFormUnsafeData(BaseTestForestValueConverter):
    """use during execute, it only parse file"""

    def test_should_parse_files(self):
        raw_data = {
            "file": "data:text/plain;name=bla.txt;base64,YWJj",
            "filelist": ["data:text/plain;name=bla.txt;base64,YWJj"],
            "string": "test string",
        }
        form_values = ForestValueConverter.make_form_unsafe_data(raw_data)
        self.assertEqual(
            form_values,
            {
                "file": File("text/plain", b"abc", "bla.txt"),
                "filelist": [File("text/plain", b"abc", "bla.txt")],
                "string": "test string",
            },
        )


class TestForestValueConverterMakeFormData(BaseTestForestValueConverter):
    def setUp(self) -> None:
        super().setUp()
        self.book_collection_action.add_action(
            "test",
            {
                "scope": "Single",
                "generate_file": False,
                "execute": Mock(),
                "form": [
                    {"type": "Collection", "collection_name": "Author", "label": "collection"},
                    {"type": "File", "label": "file"},
                    {"type": "FileList", "label": "filelist"},
                    {"type": "String", "label": "string"},
                ],
            },
        )

    def test_should_handle_collection_and_parse_files(self):
        raw_data = {
            "file": "data:text/plain;name=bla.txt;base64,YWJj",
            "filelist": ["data:text/plain;name=bla.txt;base64,YWJj"],
            "string": "test string",
            "collection": "19226e17-8430-442b-91a9-2ab96a6997a5",
        }
        unsafe_data = ForestValueConverter.make_form_unsafe_data(raw_data)
        fields = self.loop.run_until_complete(self.book_collection_action.get_form(None, "test", unsafe_data, None))
        form_values = ForestValueConverter.make_form_data(self.datasource, raw_data, fields)
        self.assertEqual(
            form_values,
            {
                "collection": [UUID("19226e17-8430-442b-91a9-2ab96a6997a5")],
                "file": File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None),
                "filelist": [File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None)],
                "string": "test string",
            },
        )


class TestForestValueConverterUriParsing(TestCase):
    def test_make_and_parse_uri_should_be_complementary(self):
        self.assertEqual(
            File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None),
            ForestValueConverter._parse_data_uri(
                ForestValueConverter._make_data_uri(
                    File(mime_type="text/plain", buffer=b"abc", name="bla.txt", charset=None)
                )
            ),
        )

    def test_make_and_parse_uri_should_handle_null_values(self):
        self.assertEqual(
            None,
            ForestValueConverter._parse_data_uri(ForestValueConverter._make_data_uri(None)),
        )
