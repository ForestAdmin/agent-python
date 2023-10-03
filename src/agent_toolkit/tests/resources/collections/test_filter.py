from unittest import TestCase

from forestadmin.agent_toolkit.resources.collections.filter import parse_condition_tree
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.utils.context import RequestMethod
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType


class TestFilter(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
                    filter_operators=[Operator.IN, Operator.EQUAL],
                    type=FieldType.COLUMN,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)

    def test_parse_condition_tree_should_parse_array_when_IN_operator_str(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "filters": '{"field":"title","operator":"in","value":"Foundation,Harry Potter"}',
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        condition_tree = parse_condition_tree(request)
        self.assertEqual(condition_tree.value, ["Foundation", "Harry Potter"])

    def test_parse_condition_tree_should_parse_array_when_IN_operator_int(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "filters": '{"field":"id","operator":"in","value":"1,2"}',
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        condition_tree = parse_condition_tree(request)
        self.assertEqual(condition_tree.value, [1, 2])
