import asyncio
import sys
from unittest import TestCase

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.publication.datasource import PublicationDataSourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToOne,
    Operator,
    PrimitiveType,
)


class TestPublicationDatasourceDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),
                "author_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "persons": ManyToMany(
                    type=FieldType.MANY_TO_MANY,
                    origin_key="book_id",
                    origin_key_target="id",
                    foreign_key="person_id",
                    foreign_key_target="id",
                    foreign_collection="Person",
                    through_collection="BookPerson",
                ),
            }
        )
        cls.collection_book_person = Collection("BookPerson", cls.datasource)
        cls.collection_book_person.add_fields(
            {
                "person_id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book_id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Book",
                    foreign_key="book_id",
                    foreign_key_target="id",
                ),
                "person": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Person",
                    foreign_key="person_id",
                    foreign_key_target="id",
                ),
            }
        )

        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book": OneToOne(
                    origin_key="author_id", origin_key_target="id", foreign_collection="Book", type=FieldType.ONE_TO_ONE
                ),
                "books": ManyToMany(
                    origin_key="person_id",
                    origin_key_target="id",
                    foreign_key="book_id",
                    foreign_key_target="id",
                    foreign_collection="Book",
                    through_collection="BookPerson",
                    type=FieldType.MANY_TO_MANY,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_book_person)
        cls.datasource.add_collection(cls.collection_person)

        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

    def test_should_return_all_collections_when_no_parameter_is_provided(self):
        decorated_datasource = PublicationDataSourceDecorator(self.datasource)
        self.assertEqual(decorated_datasource.get_collection("Book").name, self.datasource.get_collection("Book").name)
        self.assertEqual(
            decorated_datasource.get_collection("Person").name, self.datasource.get_collection("Person").name
        )

    def test_keep_collections_matching_should_throw_if_name_is_unknown(self):
        decorated_datasource = PublicationDataSourceDecorator(self.datasource)
        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Collection 'unknown' not found",
            decorated_datasource.keep_collections_matching,
            ["unknown"],
        )
        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Collection 'unknown' not found",
            decorated_datasource.keep_collections_matching,
            [],
            ["unknown"],
        )

    def test_keep_collections_matching_should_remove_book_person_collection(self):
        decorated_datasource = PublicationDataSourceDecorator(self.datasource)
        decorated_datasource.keep_collections_matching(["Book", "Person"])

        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Collection BookPerson was removed",
            decorated_datasource.get_collection,
            "BookPerson",
        )

        self.assertNotIn("persons", decorated_datasource.get_collection("Book").schema["fields"].keys())
        self.assertNotIn("books", decorated_datasource.get_collection("Person").schema["fields"].keys())

    def test_keep_collections_matching_should_remove_books_collection(self):
        decorated_datasource = PublicationDataSourceDecorator(self.datasource)
        decorated_datasource.keep_collections_matching([], ["Book"])

        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Collection Book was removed",
            decorated_datasource.get_collection,
            "Book",
        )

        self.assertNotIn("book", decorated_datasource.get_collection("BookPerson").schema["fields"].keys())
        self.assertNotIn("book", decorated_datasource.get_collection("Person").schema["fields"].keys())
