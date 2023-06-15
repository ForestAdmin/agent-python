from unittest import TestCase

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.proxy.collection import ProxyMixin
from forestadmin.datasource_toolkit.decorators.schema.collection import SchemaMixin
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType


class DecoratedCollectionMock(SchemaMixin, ProxyMixin):
    pass


class TestSchemaCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER, is_primary_key=True, is_read_only=True, type=FieldType.COLUMN
                ),
                "author_id": Column(column_type=PrimitiveType.STRING, is_read_only=True, type=FieldType.COLUMN),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "sub_title": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )

    def test_override_schema(self):
        decorated_collection_book = DecoratedCollectionMock(self.collection_book, self.datasource)
        decorated_collection_book.override_schema("countable", False)

        assert self.collection_book.schema["countable"] is True
        assert decorated_collection_book.schema["countable"] is False
