import datetime
import os
import sys
from unittest.mock import Mock, patch

from forestadmin.datasource_django.exception import DjangoNativeDriver

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from django.test import TestCase, override_settings
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, DateOperation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator as ConditionTreeAggregator,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    ConditionTreeBranch,
    ConditionTreeLeaf,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from test_app.models import Book, Person, Rating
from test_project_datasource.db_router import DbRouter


class TestDjangoCollectionCreation(TestCase):
    def setUp(self) -> None:
        self.datasource = Mock(DjangoDatasource)

    def test_creation_should_introspect_given_model(self):
        with patch(
            "forestadmin.datasource_django.collection.DjangoCollectionFactory.build",
            return_value={"actions": {}, "fields": {}, "searchable": False, "segments": []},
        ) as mock_factory_build:
            DjangoCollection(self.datasource, Book)
            mock_factory_build.assert_called_once_with(Book)

    def test_model_property_should_return_model_instance(self):
        collection = DjangoCollection(self.datasource, Book)
        self.assertEqual(collection.model, Book)


class TestDjangoCollectionCRUDList(TestCase):
    fixtures = ["person.json", "book.json"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.datasource = Mock(DjangoDatasource)

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
        self.book_collection = DjangoCollection(self.datasource, Book)

    async def test_list_should_list_all_records_of_a_collection(self):
        ret = await self.book_collection.list(self.mocked_caller, PaginatedFilter({}), Projection("id", "name"))

        self.assertEqual(ret, [{"id": 1, "name": "Foundation"}, {"id": 2, "name": "Harry Potter"}])

    async def test_list_should_work_with_relation(self):
        ret = await self.book_collection.list(
            self.mocked_caller, PaginatedFilter({}), Projection("id", "name", "author:first_name")
        )

        self.assertEqual(
            ret,
            [
                {"id": 1, "name": "Foundation", "author": {"first_name": "Isaac"}},
                {"id": 2, "name": "Harry Potter", "author": {"first_name": "J.K."}},
            ],
        )

    async def test_list_should_work_with_condition_tree(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeBranch(
                        ConditionTreeAggregator.AND,
                        [
                            ConditionTreeBranch(
                                ConditionTreeAggregator.OR,
                                [
                                    ConditionTreeLeaf("name", Operator.EQUAL, "Foundation"),
                                    ConditionTreeLeaf("author:first_name", Operator.EQUAL, "J.K."),
                                ],
                            ),
                            ConditionTreeLeaf("author:last_name", Operator.PRESENT),
                        ],
                    )
                }
            ),
            Projection("id", "name"),
        )

        self.assertEqual(ret, [{"id": 1, "name": "Foundation"}, {"id": 2, "name": "Harry Potter"}])

    async def test_list_should_work_with_pagination_and_sort(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"page": Page(skip=0, limit=1), "sort": Sort([{"field": "id", "ascending": False}])}),
            Projection("id", "name"),
        )

        self.assertEqual(ret, [{"id": 2, "name": "Harry Potter"}])

    async def test_list_should_work_with_null_relations(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "Unknown Book")}),
            Projection("id", "name", "author:first_name"),
        )

        self.assertEqual(
            ret,
            [
                {"id": 3, "name": "Unknown Book", "author": {}},
            ],
        )


class TestDjangoCollectionCRUDAggregateBase(TestCase):
    fixtures = ["person.json", "book.json", "rating.json"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.datasource = Mock(DjangoDatasource)

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
        self.book_collection = DjangoCollection(self.datasource, Book)
        self.person_collection = DjangoCollection(self.datasource, Person)
        self.rating_collection = DjangoCollection(self.datasource, Rating)


class TestDjangoCollectionCRUDAggregateNoGroupNoAggregateField(TestDjangoCollectionCRUDAggregateBase):
    async def test_aggregate_should_work(self):
        """typically the count http request"""
        ret = await self.book_collection.aggregate(self.mocked_caller, Filter({}), Aggregation({"operation": "Count"}))
        self.assertEqual(ret, [{"value": 2, "group": {}}])

    async def test_aggregate_should_work_with_condition_tree(self):
        """typically the count http request"""
        ret = await self.book_collection.aggregate(
            self.mocked_caller,
            Filter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "Harry Potter")}),
            Aggregation({"operation": "Count"}),
        )
        self.assertEqual(ret, [{"value": 1, "group": {}}])


class TestDjangoCollectionCRUDAggregateNoGroup(TestDjangoCollectionCRUDAggregateBase):
    async def test_should_work_with_avg(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Avg", "field": "rating"}),
        )
        self.assertEqual(ret, [{"value": 3.4, "group": {}}])

    async def test_should_work_with_sum(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Sum", "field": "rating"}),
        )
        self.assertEqual(ret, [{"value": 17, "group": {}}])

    async def test_should_work_with_min(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Min", "field": "rating"}),
        )
        self.assertEqual(ret, [{"value": 1, "group": {}}])

    async def test_should_work_with_max(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Max", "field": "rating"}),
        )
        self.assertEqual(ret, [{"value": 5, "group": {}}])


class TestDjangoCollectionCRUDAggregateNoAggregateField(TestDjangoCollectionCRUDAggregateBase):
    async def test_should_work_with_count(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Count", "groups": [{"field": "book:name"}]}),
        )
        self.assertEqual(
            ret,
            [
                {"value": 4, "group": {"book:name": "Foundation"}},
                {"value": 1, "group": {"book:name": "Harry Potter"}},
            ],
        )


class TestDjangoCollectionCRUDAggregateNoAggregateOperation(TestDjangoCollectionCRUDAggregateBase):
    async def test_should_work_with_avg(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Avg", "field": "rating", "groups": [{"field": "book:name"}]}),
        )
        self.assertEqual(
            ret,
            [
                {"value": 5, "group": {"book:name": "Harry Potter"}},
                {"value": 3, "group": {"book:name": "Foundation"}},
            ],
        )

    async def test_should_work_with_max(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Max", "field": "rating", "groups": [{"field": "book:name"}]}),
        )
        self.assertEqual(
            ret,
            [
                {"value": 5, "group": {"book:name": "Harry Potter"}},
                {"value": 5, "group": {"book:name": "Foundation"}},
            ],
        )

    async def test_should_work_with_min(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Min", "field": "rating", "groups": [{"field": "book:name"}]}),
        )
        self.assertEqual(
            ret,
            [
                {"value": 5, "group": {"book:name": "Harry Potter"}},
                {"value": 1, "group": {"book:name": "Foundation"}},
            ],
        )

    async def test_should_work_with_sum(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation({"operation": "Sum", "field": "rating", "groups": [{"field": "book:name"}]}),
        )
        self.assertEqual(
            ret,
            [
                {"value": 12, "group": {"book:name": "Foundation"}},
                {"value": 5, "group": {"book:name": "Harry Potter"}},
            ],
        )


class TestDjangoCollectionCRUDAggregateByDate(TestDjangoCollectionCRUDAggregateBase):
    async def test_should_work_by_year(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation(
                {
                    "operation": "Count",
                    "field": "rating",
                    "groups": [{"field": "rated_at", "operation": DateOperation.YEAR}],
                }
            ),
        )
        self.assertEqual(
            ret,
            [
                {"value": 4, "group": {"rated_at": datetime.date(2023, 1, 1)}},
                {"value": 1, "group": {"rated_at": datetime.date(2022, 1, 1)}},
            ],
        )

    async def test_should_work_by_month(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation(
                {
                    "operation": "Count",
                    "groups": [{"field": "rated_at", "operation": DateOperation.MONTH}],
                }
            ),
        )
        self.assertIn({"value": 2, "group": {"rated_at": datetime.date(2023, 2, 1)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2022, 12, 1)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2023, 1, 1)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2023, 3, 1)}}, ret)

    async def test_should_work_by_week(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation(
                {
                    "operation": "Sum",
                    "field": "rating",
                    "groups": [{"field": "rated_at", "operation": DateOperation.WEEK}],
                }
            ),
        )
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 1, 30)}}, ret)
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 2, 20)}}, ret)
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 2, 27)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2022, 12, 19)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2023, 1, 9)}}, ret)

    async def test_should_work_by_day(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation(
                {
                    "operation": "Sum",
                    "field": "rating",
                    "groups": [{"field": "rated_at", "operation": DateOperation.DAY}],
                }
            ),
        )
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 2, 2)}}, ret)
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 2, 25)}}, ret)
        self.assertIn({"value": 5, "group": {"rated_at": datetime.date(2023, 3, 2)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2022, 12, 25)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2023, 1, 12)}}, ret)


class TestDjangoCollectionCRUDCreateUpdateDelete(TestDjangoCollectionCRUDAggregateBase):
    async def test_create_should_work(self):
        ret = await self.person_collection.create(
            self.mocked_caller, [{"first_name": "J. R. R.", "last_name": "Tolkien", "birth_date": "1892-01-03"}]
        )
        self.assertEqual(
            ret,
            [
                {
                    "first_name": "J. R. R.",
                    "last_name": "Tolkien",
                    "birth_date": datetime.date(1892, 1, 3),
                    "id": ret[0]["id"],
                    "auth_user_id": None,
                }
            ],
        )

        retrieved = await self.person_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, ret[0]["id"])}),
            Projection("id", "first_name", "last_name", "birth_date", "auth_user_id"),
        )
        self.assertEqual(retrieved, ret)

    async def test_delete_should_work(self):
        await self.person_collection.create(
            self.mocked_caller, [{"first_name": "J. R. R.", "last_name": "Tolkien", "birth_date": "1892-01-03"}]
        )

        await self.person_collection.delete(
            self.mocked_caller, Filter({"condition_tree": ConditionTreeLeaf("last_name", Operator.EQUAL, "Tolkien")})
        )

        entries = await self.person_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("last_name", Operator.EQUAL, "Tolkien")}),
            Projection("id", "first_name", "last_name", "birth_date"),
        )
        self.assertEqual(len(entries), 0)

    async def test_update_should_work(self):
        await self.person_collection.delete(
            self.mocked_caller, Filter({"condition_tree": ConditionTreeLeaf("last_name", Operator.EQUAL, "Tolkien")})
        )
        await self.person_collection.create(
            self.mocked_caller,
            [
                {"first_name": "J. R. R.", "last_name": "Tolkien", "birth_date": "1892-01-03"},
                {"first_name": "J. R. R.", "last_name": "Tolkienn", "birth_date": "1892-01-03"},
                {"first_name": "J. R. R.", "last_name": "Tolkiennne", "birth_date": "1892-01-03"},
                {"first_name": "J. R. R.", "last_name": "T", "birth_date": "1892-01-03"},
            ],
        )
        await self.person_collection.update(
            self.mocked_caller,
            Filter(
                {
                    "condition_tree": ConditionTreeBranch(
                        ConditionTreeAggregator.AND,
                        [
                            ConditionTreeLeaf("first_name", Operator.EQUAL, "J. R. R."),
                            ConditionTreeLeaf("birth_date", Operator.EQUAL, "1892-01-03"),
                        ],
                    )
                }
            ),
            {"last_name": "Tolkien"},
        )

        tolkiens = await self.person_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("last_name", Operator.EQUAL, "Tolkien")}),
            Projection("id", "last_name", "first_name"),
        )

        self.assertEqual(len(tolkiens), 4)


class TestDjangoCollectionNativeDriver(TestDjangoCollectionCRUDAggregateBase):
    databases = "__all__"

    def test_native_driver_should_work(self):
        with self.book_collection.get_native_driver() as cursor:
            cursor.execute("select id, name, author_id from test_app_book where id=1")
            row = cursor.fetchone()

        self.assertEqual(row, (1, "Foundation", 1))

    def test_native_driver_should_work_and_restore_django_async_safe_variable(self):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "false"
        with self.book_collection.get_native_driver() as cursor:
            cursor.execute("select id, name, author_id from test_app_book where id=1")
            row = cursor.fetchone()
            self.assertEqual(os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"], "true")

        self.assertEqual(row, (1, "Foundation", 1))
        self.assertEqual(os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"], "false")

    def test_native_driver_should_use_db_router(self):
        def mock_db_for_read(model, **hint):
            return None

        def mock_db_for_write(model, **hint):
            return None

        with override_settings(DATABASE_ROUTERS=["test_project_datasource.db_router.DbRouter"]):
            with patch.object(DbRouter, "db_for_read", wraps=mock_db_for_read) as spy_mock_db_read:
                with patch.object(DbRouter, "db_for_write", wraps=mock_db_for_write) as spy_mock_db_write:
                    with self.book_collection.get_native_driver():
                        pass
                    spy_mock_db_read.assert_called_with(self.book_collection.model, forest_native_driver=True)
                    spy_mock_db_write.assert_called_with(self.book_collection.model, forest_native_driver=True)

    def test_native_driver_should_return_correct_mapper_according_to_use_db_router(self):
        def mock_db_for_read(model, **hint):
            return "other"

        def mock_db_for_write(model, **hint):
            return "other"

        with override_settings(DATABASE_ROUTERS=["test_project_datasource.db_router.DbRouter"]):
            with patch.object(DbRouter, "db_for_read", wraps=mock_db_for_read):
                with patch.object(DbRouter, "db_for_write", wraps=mock_db_for_write):
                    with self.book_collection.get_native_driver() as cursor:
                        self.assertEqual(cursor.db.alias, "other")

    def test_native_driver_should_raise_if_db_router_return_different_db_for_read_and_write(self):
        def mock_db_for_read(model, **hint):
            return "default"

        def mock_db_for_write(model, **hint):
            return "other"

        with override_settings(DATABASE_ROUTERS=["test_project_datasource.db_router.DbRouter"]):
            with patch.object(DbRouter, "db_for_read", wraps=mock_db_for_read):
                with patch.object(DbRouter, "db_for_write", wraps=mock_db_for_write):
                    self.assertRaisesRegex(
                        DjangoNativeDriver,
                        "Cannot choose database between return db router. "
                        "Read database is 'default', and write database is 'other'.",
                        self.book_collection.get_native_driver,
                    )
