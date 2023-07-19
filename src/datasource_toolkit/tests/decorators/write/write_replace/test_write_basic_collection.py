import asyncio
from unittest import TestCase

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_replace_collection import (
    WriteReplaceCollection,
)
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType


class TestWriteBasicCollection(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN, is_read_only=True
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    filter_operators=[Operator.PRESENT],
                    is_read_only=True,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_book)

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, WriteReplaceCollection)
        self.collection_book_decorated = self.datasource_decorator.get_collection("Book")

    def test_replace_field_writing_should_raise_on_non_existent_field(self):
        self.assertRaisesRegex(
            ForestException,
            r"The given field '_dont_exists' does not exists on the Book collection\.",
            self.collection_book_decorated.replace_field_writing,
            "_dont_exists",
            lambda val, ctx: {},
        )

    def test_should_mark_field_as_writable_when_handler_is_defined(self):
        assert self.collection_book_decorated.schema["fields"]["title"]["is_read_only"] is True
        self.collection_book_decorated.replace_field_writing("title", lambda val, ctx: {})
        assert self.collection_book_decorated.schema["fields"]["title"]["is_read_only"] is False

    def test_should_mark_field_as_writable_when_handler_is_null(self):
        self.collection_book_decorated.replace_field_writing("title", None)
        assert self.collection_book_decorated.schema["fields"]["title"]["is_read_only"] is True
