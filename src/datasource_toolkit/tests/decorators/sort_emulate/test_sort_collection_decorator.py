import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.sort_emulate.collections import SortCollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort


class BaseTestSortEmulateCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_books = Collection("Books", cls.datasource)
        cls.collection_books.add_fields(
            {
                "id": Column(
                    type=FieldType.COLUMN,
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    is_sortable=False,
                ),
                "author_id": Column(column_type=PrimitiveType.UUID, type=FieldType.COLUMN),
                "author": ManyToOne(type=FieldType.MANY_TO_ONE, foreign_collection="Persons", foreign_key="author_id"),
            }
        )
        cls.book_records = [
            {
                "id": 1,
                "author_id": 1,
                "author": {"id": 1, "first_name": "Isaac", "last_name": "Asimov"},
                "title": "Foundation",
            },
            {
                "id": 2,
                "author_id": 2,
                "author": {"id": 2, "first_name": "Edward O.", "last_name": "Thorp"},
                "title": "Beat the dealer",
            },
            {
                "id": 3,
                "author_id": 3,
                "author": {"id": 3, "first_name": "Roberto", "last_name": "Saviano"},
                "title": "Gomorrah",
            },
        ]

        async def mocked_book_list(caller: User, filter_: PaginatedFilter, projection: Projection):
            rows = [*cls.book_records]
            if filter_ and filter_.condition_tree:
                rows = filter_.condition_tree.filter(rows, cls.collection_books, caller.timezone)
            if filter_ and filter_.sort:
                rows = filter_.sort.apply(rows)
            if filter_ and filter_.page:
                rows = filter_.page.apply(rows)
            return projection.apply(rows)

        cls.collection_books.list = AsyncMock(side_effect=mocked_book_list)

        cls.collection_persons = Collection("Persons", cls.datasource)
        cls.collection_persons.add_fields(
            {
                "id": Column(
                    type=FieldType.COLUMN,
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                ),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN, is_sortable=False),
            }
        )

        cls.datasource.add_collection(cls.collection_books)
        cls.datasource.add_collection(cls.collection_persons)

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
        self.decorated_datasource = DatasourceDecorator(self.datasource, SortCollectionDecorator)
        self.decorated_books = self.decorated_datasource.get_collection("Books")
        self.decorated_persons = self.decorated_datasource.get_collection("Persons")


class TestSortEmulateCollectionDecorator(BaseTestSortEmulateCollectionDecorator):
    def test_should_throw_if_field_does_not_exist(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Column not found: Books\._don't_exists",
            self.decorated_books.emulate_field_sorting,
            "_don't_exists",
        )

    def test_should_throw_if_field_is_relation(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Unexpected field type: Books.author \(found FieldType.MANY_TO_ONE expected Column\)",
            self.decorated_books.emulate_field_sorting,
            "author",
        )


class TestSortEmulateOnBookTitle(BaseTestSortEmulateCollectionDecorator):
    def setUp(self) -> None:
        super().setUp()
        self.decorated_books.emulate_field_sorting("title")

    def test_should_update_schema(self):
        schema = self.decorated_books.schema["fields"]["title"]
        self.assertTrue(schema["is_sortable"])

    def test_should_work_in_ascending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "title", "ascending": True}])}),
                Projection("id", "title"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 2, "title": "Beat the dealer"},
                {"id": 1, "title": "Foundation"},
                {"id": 3, "title": "Gomorrah"},
            ],
        )

    def test_should_work_in_descending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "title", "ascending": False}])}),
                Projection("id", "title"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 3, "title": "Gomorrah"},
                {"id": 1, "title": "Foundation"},
                {"id": 2, "title": "Beat the dealer"},
            ],
        )

    def test_should_work_with_pagination(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "title", "ascending": False}]), "page": Page(2, 1)}),
                Projection("id", "title"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 2, "title": "Beat the dealer"},
            ],
        )


class TestSortEmulateOnBookAuthorLastName(BaseTestSortEmulateCollectionDecorator):
    def setUp(self) -> None:
        super().setUp()
        self.decorated_persons.emulate_field_sorting("last_name")

    def test_should_update_schema(self):
        schema = self.decorated_persons.schema["fields"]["last_name"]
        self.assertTrue(schema["is_sortable"])

    def test_should_work_in_ascending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "author:last_name", "ascending": True}])}),
                Projection("id", "title", "author:last_name"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 1, "title": "Foundation", "author": {"last_name": "Asimov"}},
                {"id": 3, "title": "Gomorrah", "author": {"last_name": "Saviano"}},
                {"id": 2, "title": "Beat the dealer", "author": {"last_name": "Thorp"}},
            ],
        )

    def test_should_work_in_descending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "author:last_name", "ascending": False}])}),
                Projection("id", "title", "author:last_name"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 2, "title": "Beat the dealer", "author": {"last_name": "Thorp"}},
                {"id": 3, "title": "Gomorrah", "author": {"last_name": "Saviano"}},
                {"id": 1, "title": "Foundation", "author": {"last_name": "Asimov"}},
            ],
        )


class TestSortEmulateReplaceSort(BaseTestSortEmulateCollectionDecorator):
    def setUp(self) -> None:
        super().setUp()
        self.decorated_books.replace_field_sorting("title", [{"field": "author:last_name", "ascending": True}])

    def test_schema_should_be_updated(self):
        schema = self.decorated_books.schema["fields"]["title"]
        self.assertTrue(schema["is_sortable"])

    def test_should_work_in_ascending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "title", "ascending": True}])}),
                Projection("id", "title", "author:last_name"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 1, "title": "Foundation", "author": {"last_name": "Asimov"}},
                {"id": 3, "title": "Gomorrah", "author": {"last_name": "Saviano"}},
                {"id": 2, "title": "Beat the dealer", "author": {"last_name": "Thorp"}},
            ],
        )

    def test_should_work_in_descending_order(self):
        records = self.loop.run_until_complete(
            self.decorated_books.list(
                self.mocked_caller,
                PaginatedFilter({"sort": Sort([{"field": "title", "ascending": False}])}),
                Projection("id", "title", "author:last_name"),
            )
        )

        self.assertEqual(
            records,
            [
                {"id": 2, "title": "Beat the dealer", "author": {"last_name": "Thorp"}},
                {"id": 3, "title": "Gomorrah", "author": {"last_name": "Saviano"}},
                {"id": 1, "title": "Foundation", "author": {"last_name": "Asimov"}},
            ],
        )
