import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.publication_field.datasource import PublicationDataSourceDecorator
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


class TestPublicationCollectionDecorator(TestCase):
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

    def setUp(self) -> None:
        self.datasource_decorator = PublicationDataSourceDecorator(self.datasource)

        self.decorated_collection_person = self.datasource_decorator.get_collection("Person")
        self.decorated_collection_person_book = self.datasource_decorator.get_collection("BookPerson")
        self.decorated_collection_book = self.datasource_decorator.get_collection("Book")

    def test_change_visibility_error_on_non_existent_field(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳No such field 'unknown'",
            self.decorated_collection_person.change_field_visibility,
            "unknown",
            False,
        )

    def test_change_visibility_error_on_primary_key_field(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot hide primary key",
            self.decorated_collection_person.change_field_visibility,
            "id",
            False,
        )

    def test_schema_dont_update_if_no_changes(self):
        assert self.decorated_collection_person_book.schema == self.collection_book_person.schema
        assert self.decorated_collection_book.schema == self.collection_book.schema
        assert self.decorated_collection_person.schema == self.collection_person.schema

    def test_schema_dont_move_after_hide_and_show(self):
        self.decorated_collection_person.change_field_visibility("book", False)
        self.decorated_collection_person.change_field_visibility("book", True)

        assert self.decorated_collection_person.schema == self.collection_person.schema

        self.decorated_collection_book.change_field_visibility("title", False)
        assert "title" not in self.decorated_collection_book.schema["fields"]

    def test_hiding_does_not_affect_other_fields(self):
        self.decorated_collection_book.change_field_visibility("title", False)

        field_names = self.decorated_collection_book.schema["fields"].keys()
        assert "id" in field_names
        assert "author_id" in field_names
        assert "author" in field_names
        assert "persons" in field_names

    def test_hiding_does_not_affect_other_collections(self):
        self.decorated_collection_book.change_field_visibility("title", False)

        assert self.decorated_collection_person_book.schema == self.collection_book_person.schema
        assert self.decorated_collection_person.schema == self.collection_person.schema

    def test_create_should_not_return_hidden_fields(self):
        # create = {"id": 1, "author_id": 2, "title": "foundation"}
        create = {"id": 1, "author_id": 2}
        self.decorated_collection_book.change_field_visibility("title", False)

        with patch.object(self.collection_book, "create", new_callable=AsyncMock, return_value=[create]):
            created = self.loop.run_until_complete(self.decorated_collection_book.create(self.mocked_caller, [create]))

        assert created == [{"id": 1, "author_id": 2}]

    def test_hiding_fk_should_hide_fk(self):
        self.decorated_collection_book.change_field_visibility("author_id", False)

        assert "author_id" not in self.decorated_collection_person_book.schema["fields"]

    def test_hiding_fk_should_hide_linked_relations(self):
        self.decorated_collection_book.change_field_visibility("author_id", False)

        assert "author" not in self.decorated_collection_person_book.schema["fields"]
