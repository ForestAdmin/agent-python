import asyncio
from unittest import TestCase
from unittest.mock import patch

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.context.relaxed_wrappers.collection import RelaxedCollection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType


class TestRelaxedCollection(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.IN, Operator.EQUAL]),
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN],
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_book)

    def test_get_native_driver_should_return_native_driver_from_collection(self):
        relaxed_collection = RelaxedCollection(self.collection_book)

        with patch.object(self.collection_book, "get_native_driver", return_value="native_driver"):
            self.assertEqual(relaxed_collection.get_native_driver(), "native_driver")
