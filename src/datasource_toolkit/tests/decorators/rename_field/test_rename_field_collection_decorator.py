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
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.rename_field.collections import (
    RenameCollectionException,
    RenameFieldCollectionDecorator,
)
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToOne,
    Operator,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, PlainAggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort


class TestRenameFieldCollectionDecorator(TestCase):
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
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "ratings": PolymorphicOneToMany(
                    foreign_collection="Rating",
                    origin_key="target_id",
                    origin_key_target="id",
                    origin_type_field="target_type",
                    origin_type_value="Bar",
                    type=FieldType.POLYMORPHIC_ONE_TO_MANY,
                ),
            }
        )

        cls.collection_rating = Collection("Rating", cls.datasource)
        cls.collection_rating.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "rating": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "target_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "target_type": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "target": PolymorphicManyToOne(
                    foreign_collections=["Person"],
                    foreign_key="target_id",
                    foreign_key_targets={"Person": "id"},
                    foreign_key_type_field="target_type",
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_book_person)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_rating)

        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
            request={"ip": "127.0.0.1"},
        )

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, RenameFieldCollectionDecorator)

        self.decorated_collection_person = self.datasource_decorator.get_collection("Person")
        self.decorated_collection_person_book = self.datasource_decorator.get_collection("BookPerson")
        self.decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.decorated_collection_rating = self.datasource_decorator.get_collection("Rating")

    def test_rename_unexistent_field(self):
        self.assertRaisesRegex(
            RenameCollectionException,
            r"🌳🌳No such field 'Book.unknown', choices are id, title, author_id, author, persons",
            self.decorated_collection_book.rename_field,
            "unknown",
            "new_title",
        )

    def test_rename_already_rename_field(self):
        self.decorated_collection_book.rename_field(
            "id",
            "key",
        )
        self.assertRaisesRegex(
            RenameCollectionException,
            r"🌳🌳No such field 'Book.id', choices are id, title, author_id, author, persons",
            self.decorated_collection_book.rename_field,
            "id",
            "primary_key",
        )

    def test_rename_multiple_times_same_field(self):
        self.decorated_collection_book.rename_field("id", "key")
        self.decorated_collection_book.rename_field("key", "primary_key")
        self.decorated_collection_book.rename_field("primary_key", "primary_id")
        self.decorated_collection_book.rename_field("primary_id", "id")

        assert self.decorated_collection_book.schema == self.collection_book.schema

    def test_should_raise_if_renaming_a_field_referenced_in_a_polymorphic_relation(self):
        self.assertRaisesRegex(
            RenameCollectionException,
            r"🌳🌳🌳Cannot rename 'Rating.target_type', because it's implied  in a polymorphic relation 'Rating.target'",
            self.decorated_collection_rating.rename_field,
            "target_type",
            "whatever",
        )
        self.assertRaisesRegex(
            RenameCollectionException,
            r"🌳🌳🌳Cannot rename 'Rating.target_id', because it's implied  in a polymorphic relation 'Rating.target'",
            self.decorated_collection_rating.rename_field,
            "target_id",
            "whatever",
        )

    def test_create_should_work_as_passthrough_without_renaming(self):
        record = {"id": 1, "author_id": 1, "title": "foundation"}

        with patch.object(self.collection_book, "create", new_callable=AsyncMock, return_value=[record]) as mock_create:
            created = self.loop.run_until_complete(
                self.decorated_collection_book.create(self.mocked_caller, [{"author_id": 1, "title": "foundation"}])
            )
            mock_create.assert_awaited_with(self.mocked_caller, [{"author_id": 1, "title": "foundation"}])

        assert created[0] == record

    def test_create_should_rewrite_record_when_renaming(self):
        record = {"id": 1, "author_id": 1, "title": "foundation"}
        self.decorated_collection_book.rename_field("id", "primary_key")

        with patch.object(self.collection_book, "create", new_callable=AsyncMock, return_value=[record]) as mock_create:
            created = self.loop.run_until_complete(
                self.decorated_collection_book.create(
                    self.mocked_caller, [{"primary_key": 1, "author_id": 1, "title": "foundation"}]
                )
            )
            mock_create.assert_awaited_with(self.mocked_caller, [{"id": 1, "author_id": 1, "title": "foundation"}])

        assert created[0] == {"primary_key": 1, "author_id": 1, "title": "foundation"}

    def test_list_should_work_as_passthrough_without_renaming(self):
        records = [
            {"id": 1, "author": {"id": 1, "first_name": "Isaac"}, "title": "foundation"},
            {"id": 2, "author": {"id": 2, "first_name": "Edward O."}, "title": "Beat the dealer"},
        ]

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=records):
            listed = self.loop.run_until_complete(
                self.decorated_collection_book.list(
                    self.mocked_caller, PaginatedFilter({}), Projection("id", "author:first_name", "title")
                )
            )

        assert listed == records

    def test_list_should_rewrite_filter_projection_sort_record_when_renaming(self):
        records = [
            {"id": 1, "author": {"id": 1, "first_name": "Isaac"}, "title": "foundation"},
            {"id": 2, "author": {"id": 2, "first_name": "Edward O."}, "title": "Beat the dealer"},
        ]
        self.decorated_collection_book.rename_field("id", "primary_key")
        self.decorated_collection_book.rename_field("author", "novel_author")

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=records) as mock_list:
            listed = self.loop.run_until_complete(
                self.decorated_collection_book.list(
                    self.mocked_caller,
                    PaginatedFilter(
                        {
                            "condition_tree": ConditionTreeLeaf("primary_key", Operator.GREATER_THAN, 0),
                            "sort": Sort(
                                [
                                    {"field": "primary_key", "ascending": False},
                                    {"field": "novel_author:first_name", "ascending": True},
                                ],
                            ),
                        },
                    ),
                    Projection("primary_key", "novel_author:first_name", "title"),
                )
            )

            mock_list.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter(
                    {
                        "condition_tree": ConditionTreeLeaf("id", Operator.GREATER_THAN, 0),
                        "sort": Sort(
                            [
                                {"field": "id", "ascending": False},
                                {"field": "author:first_name", "ascending": True},
                            ]
                        ),
                    }
                ),
                Projection("id", "author:first_name", "title"),
            )

        assert listed == [
            {"primary_key": 1, "novel_author": {"id": 1, "first_name": "Isaac"}, "title": "foundation"},
            {"primary_key": 2, "novel_author": {"id": 2, "first_name": "Edward O."}, "title": "Beat the dealer"},
        ]

    def test_list_should_rewrite_record_wth_none_when_renaming(self):
        records = [
            {"id": 1, "author": None, "title": "foundation"},
        ]
        self.decorated_collection_book.rename_field("id", "primary_key")
        self.decorated_collection_book.rename_field("author", "novel_author")

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=records):
            listed = self.loop.run_until_complete(
                self.decorated_collection_book.list(
                    self.mocked_caller,
                    PaginatedFilter({}),
                    Projection("primary_key", "novel_author:first_name", "title"),
                )
            )

        assert listed == [
            {"primary_key": 1, "novel_author": None, "title": "foundation"},
        ]

    def test_update_should_work_as_passthrough_without_renaming(self):
        record = {"id": 1, "title": "foundation"}

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_update:
            self.loop.run_until_complete(
                self.decorated_collection_book.update(self.mocked_caller, PaginatedFilter({}), record)
            )
            mock_update.assert_awaited_with(self.mocked_caller, PaginatedFilter({}), record)

    def test_update_should_rewrite_filter_patch_when_renaming(self):
        record = {"id": 1, "title": "foundation"}
        self.decorated_collection_book.rename_field("id", "primary_key")

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_update:
            self.loop.run_until_complete(
                self.decorated_collection_book.update(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("primary_key", Operator.EQUAL, 1)}),
                    record,
                )
            )
            mock_update.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)}),
                {"id": 1, "title": "foundation"},
            )

    def test_aggregate_should_work_as_passthrough_without_renaming(self):
        result = [{"value": 34, "group": {}}]
        aggregate = Aggregation(PlainAggregation(operation="Count"))
        _filter = PaginatedFilter({})

        with patch.object(self.collection_book, "aggregate", new_callable=AsyncMock, return_value=result):
            returned = self.loop.run_until_complete(
                self.decorated_collection_book.aggregate(self.mocked_caller, _filter, aggregate)
            )
        assert returned == result

    def test_aggregate_should_rewrite_filter_records_when_renaming(self):
        self.decorated_collection_book.rename_field("author", "novel_author")
        result = [{"value": 34, "group": {"author:first_name": "foo"}}]
        aggregate = Aggregation(
            PlainAggregation(operation="Count", field="id", groups=[{"field": "novel_author:first_name"}])
        )
        _filter = PaginatedFilter(
            {"condition_tree": ConditionTreeLeaf("novel_author:first_name", Operator.NOT_EQUAL, "abc")}
        )

        with patch.object(
            self.collection_book, "aggregate", new_callable=AsyncMock, return_value=result
        ) as mock_aggregate:
            returned = self.loop.run_until_complete(
                self.decorated_collection_book.aggregate(self.mocked_caller, _filter, aggregate)
            )
            mock_aggregate.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:first_name", Operator.NOT_EQUAL, "abc")}),
                Aggregation(PlainAggregation(operation="Count", field="id", groups=[{"field": "author:first_name"}])),
                None,
            )

        assert returned == [{"value": 34, "group": {"novel_author:first_name": "foo"}}]

    def test_delete_should_rewrite_filter(self):
        self.decorated_collection_book.rename_field("id", "primary_key")
        _filter = PaginatedFilter({"condition_tree": ConditionTreeLeaf("primary_key", Operator.EQUAL, 1)})

        with patch.object(self.collection_book, "delete", new_callable=AsyncMock) as mock_delete:
            self.loop.run_until_complete(self.decorated_collection_book.delete(self.mocked_caller, _filter))

            mock_delete.assert_awaited_with(
                self.mocked_caller, PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})
            )

    def test_columns_rename_in_schema_when_renaming_fk(self):
        self.decorated_collection_person_book.rename_field("book_id", "novel_id")
        self.decorated_collection_person_book.rename_field("person_id", "author_id")

        fields = self.decorated_collection_person_book.schema["fields"]

        assert fields["author_id"]["type"] == FieldType.COLUMN
        assert fields["novel_id"]["type"] == FieldType.COLUMN

        assert "book_id" not in fields
        assert "person_id" not in fields

    def test_relation_should_be_updated_in_all_collection_when_renaming_fk(self):
        self.decorated_collection_person_book.rename_field("book_id", "novel_id")
        self.decorated_collection_person_book.rename_field("person_id", "author_id")

        person_book_fields = self.decorated_collection_person_book.schema["fields"]
        person_fields = self.decorated_collection_person.schema["fields"]
        book_fields = self.decorated_collection_book.schema["fields"]

        assert book_fields["persons"]["foreign_key"] == "author_id"
        assert book_fields["persons"]["origin_key"] == "novel_id"
        assert person_book_fields["book"]["foreign_key"] == "novel_id"
        assert person_book_fields["person"]["foreign_key"] == "author_id"
        assert person_fields["book"]["origin_key"] == "author_id"

    def test_when_renaming_pk_should_update_all_collections(self):
        self.decorated_collection_book.rename_field("id", "new_book_id")
        self.decorated_collection_person.rename_field("id", "new_person_id")

        book_fields = self.decorated_collection_book.schema["fields"]
        person_fields = self.decorated_collection_person.schema["fields"]
        person_book_fields = self.decorated_collection_person_book.schema["fields"]

        self.assertEqual(book_fields["persons"]["foreign_key_target"], "new_person_id")
        self.assertEqual(book_fields["persons"]["origin_key_target"], "new_book_id")

        self.assertEqual(book_fields["author"]["foreign_key_target"], "new_person_id")
        self.assertEqual(person_fields["book"]["origin_key_target"], "new_person_id")

        self.assertEqual(person_book_fields["book"]["foreign_key_target"], "new_book_id")
        self.assertEqual(person_book_fields["person"]["foreign_key_target"], "new_person_id")
