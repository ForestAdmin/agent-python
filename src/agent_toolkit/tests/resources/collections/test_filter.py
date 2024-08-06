from unittest import TestCase
from unittest.mock import patch

from forestadmin.agent_toolkit.resources.collections.filter import parse_condition_tree, parse_projection, parse_sort
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.utils.context import RequestMethod
from forestadmin.datasource_toolkit.collections import Collection, CollectionException
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToOne,
    Operator,
    PolymorphicManyToOne,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator
from forestadmin.datasource_toolkit.validations.projection import ProjectionValidator


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
                "author": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Person",
                    foreign_key="auhtor_id",
                    foreign_key_targe="id",
                ),
                "author_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.IN, Operator.EQUAL]),
                ),
            }
        )

        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.IN, Operator.EQUAL]),
                ),
                "firstname": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.IN, Operator.EQUAL, Operator.STARTS_WITH],
                    type=FieldType.COLUMN,
                ),
                "lastname": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                    type=FieldType.COLUMN,
                ),
            }
        )

        cls.collection_tag = Collection("Tag", cls.datasource)
        cls.collection_tag.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.IN, Operator.EQUAL]),
                ),
                "tag": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=set([Operator.IN, Operator.EQUAL, Operator.STARTS_WITH]),
                    type=FieldType.COLUMN,
                ),
                "taggable_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    filter_operators=set([Operator.IN, Operator.EQUAL]),
                    type=FieldType.COLUMN,
                ),
                "taggable_type": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=set([Operator.IN, Operator.EQUAL, Operator.STARTS_WITH]),
                    type=FieldType.COLUMN,
                ),
                "taggable": PolymorphicManyToOne(
                    foreign_collections=["Book", "Person"],
                    foreign_key="taggable_id",
                    foreign_key_targets={"Book": "id", "Person": "id"},
                    foreign_key_type_field="taggable_type",
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_tag)


class TestFilterConditionTree(TestFilter):
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

    def test_parse_condition_tree_should_parse_complex_condition_tree(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "filters": '{"aggregator": "or","conditions": [{"field":"id","operator":"in","value":"1,2"}, '
                '{"field":"author:firstname","operator":"starts_with","value":"A"}]}',
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        condition_tree = parse_condition_tree(request)
        self.assertEqual(condition_tree.aggregator, Aggregator.OR)
        self.assertEqual(condition_tree.conditions[0].operator, Operator.IN)
        self.assertEqual(condition_tree.conditions[0].value, [1, 2])
        self.assertEqual(condition_tree.conditions[1].operator, Operator.STARTS_WITH)
        self.assertEqual(condition_tree.conditions[1].value, "A")

    def test_parse_condition_tree_should_parse_in_operators_with_list_and_comma_separated_values(self):
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

        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "filters": '{"field":"id","operator":"in","value":[1, 2]}',
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        condition_tree = parse_condition_tree(request)
        self.assertEqual(condition_tree.value, [1, 2])

        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "filters": '{"field":"id","operator":"in","value":["1", "2"]}',
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        condition_tree = parse_condition_tree(request)
        self.assertEqual(condition_tree.value, [1, 2])


class TestFilterProjection(TestFilter):
    def test_parse_projection_should_parse_in_query_projection(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title,author",
                "fields[author]": "id",
            },
            collection=self.collection_book,
        )
        expected_projection = ["id", "title", "author:id"]

        with patch(
            "forestadmin.agent_toolkit.resources.collections.filter.ProjectionValidator.validate",
            wraps=ProjectionValidator.validate,
        ) as spy_validate:
            projection = parse_projection(request)
            spy_validate.assert_called_once_with(self.collection_book, expected_projection)
        self.assertEqual(sorted(projection), sorted(expected_projection))

    def test_parse_projection_should_return_all_collections_field_as_projection_when_nothing_specified_in_request(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
            },
            collection=self.collection_book,
        )
        expected_projection = ["author:firstname", "author:id", "author:lastname", "author_id", "id", "title"]

        projection = parse_projection(request)
        self.assertEqual(sorted(projection), sorted(expected_projection))

    def test_parse_projection_should_raise_when_query_want_an_unexisting_field(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title,blabedoubla",
            },
            collection=self.collection_book,
        )

        self.assertRaisesRegex(CollectionException, r"Field not found 'Book.blabedoubla'", parse_projection, request)

    def test_parse_projection_should_add_a_star_to_polymorphic_many_to_one(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Tag",
            },
            collection=self.collection_tag,
        )
        expected_projection = ["id", "tag", "taggable_id", "taggable_type", "taggable:*"]

        projection = parse_projection(request)
        self.assertEqual(sorted(projection), sorted(expected_projection))


class TestFilterSort(TestFilter):
    def test_parse_sort_should_return_pk_when_nothing_set(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title",
            },
            collection=self.collection_book,
        )

        sort = parse_sort(request)
        self.assertEqual(sort, [{"field": "id", "ascending": True}])

    def test_parse_sort_should_parse_sort_from_request(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title",
                "sort": "title",
            },
            collection=self.collection_book,
        )

        sort = parse_sort(request)
        self.assertEqual(sort, [{"field": "title", "ascending": True}])

    def test_parse_sort_should_parse_descending_sort_from_request(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title",
                "sort": "-title",
            },
            collection=self.collection_book,
        )

        sort = parse_sort(request)
        self.assertEqual(sort, [{"field": "title", "ascending": False}])

    def test_parse_sort_should_parse_multiple_field_sorting(self):
        request = RequestCollection(
            method=RequestMethod.GET,
            body=None,
            query={
                "collection_name": "Book",
                "fields[Book]": "id,title",
                "sort": "-title,id",
            },
            collection=self.collection_book,
        )
        sort = parse_sort(request)
        self.assertEqual(sort, [{"field": "title", "ascending": False}, {"field": "id", "ascending": True}])
