import datetime
import os
import sys
from unittest.mock import Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from django.test import TestCase, override_settings
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_django.collection import DjangoCollection
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.datasource_django.exception import DjangoNativeDriver
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
from test_app.models import Book, Person, Rating, Tag
from test_project_datasource.db_router import DbRouter


class TestDjangoCollectionCreation(TestCase):
    def setUp(self) -> None:
        self.datasource = Mock(DjangoDatasource)

    def test_creation_should_introspect_given_model(self):
        with patch(
            "forestadmin.datasource_django.collection.DjangoCollectionFactory.build",
            return_value={"actions": {}, "fields": {}, "searchable": False, "segments": []},
        ) as mock_factory_build:
            DjangoCollection(self.datasource, Book, False)
            mock_factory_build.assert_called_once_with(Book, False)

    def test_model_property_should_return_model_instance(self):
        collection = DjangoCollection(self.datasource, Book, False)
        self.assertEqual(collection.model, Book, False)


class TestDjangoCollectionCRUDList(TestCase):
    fixtures = ["person.json", "book.json", "rating.json", "tag.json"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.datasource = DjangoDatasource()

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
        self.book_collection = DjangoCollection(self.datasource, Book, False)
        self.person_collection = DjangoCollection(self.datasource, Person, False)
        self.rating_collection = DjangoCollection(self.datasource, Rating, False)
        self.tag_collection = DjangoCollection(self.datasource, Tag, False)

    async def test_list_should_list_all_records_of_a_collection(self):
        ret = await self.book_collection.list(self.mocked_caller, PaginatedFilter({}), Projection("book_pk", "name"))

        self.assertEqual(
            ret,
            [
                {"book_pk": 1, "name": "Foundation"},
                {"book_pk": 2, "name": "Harry Potter"},
                {"book_pk": 3, "name": "Unknown Book"},
            ],
        )

    async def test_list_should_work_with_relation(self):
        ret = await self.book_collection.list(
            self.mocked_caller, PaginatedFilter({}), Projection("book_pk", "name", "author:first_name")
        )

        self.assertEqual(
            ret,
            [
                {"book_pk": 1, "name": "Foundation", "author": {"first_name": "Isaac"}},
                {"book_pk": 2, "name": "Harry Potter", "author": {"first_name": "J.K."}},
                {"book_pk": 3, "name": "Unknown Book", "author": None},
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
            Projection("book_pk", "name"),
        )

        self.assertEqual(ret, [{"book_pk": 1, "name": "Foundation"}, {"book_pk": 2, "name": "Harry Potter"}])

    async def test_list_should_work_with_pagination_and_sort(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"page": Page(skip=0, limit=1), "sort": Sort([{"field": "book_pk", "ascending": False}])}),
            Projection("book_pk", "name"),
        )

        self.assertEqual(ret, [{"book_pk": 3, "name": "Unknown Book"}])

    async def test_list_should_work_with_null_relations(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "Unknown Book")}),
            Projection("book_pk", "name", "author:first_name"),
        )

        self.assertEqual(
            ret,
            [
                {"book_pk": 3, "name": "Unknown Book", "author": None},
            ],
        )

    async def test_decimal_should_be_correctly_serialized(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "Unknown Book")}),
            Projection("book_pk", "name", "price"),
        )

        self.assertEqual(
            ret,
            [
                {"book_pk": 3, "name": "Unknown Book", "price": 3.45},
            ],
        )

    async def test_datetime_and_date_should_be_correctly_serialized(self):
        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("rating_pk", Operator.EQUAL, 1)}),
            Projection("rating_pk", "rated_at", "rating", "book:author:birth_date"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "rating": 1,
                    "rated_at": datetime.datetime(2022, 12, 25, 10, 10, 10, tzinfo=datetime.timezone.utc),
                    "book": {"author": {"birth_date": datetime.date(1920, 2, 1)}},
                },
            ],
        )

    async def test_in_and_not_in_should_works_contains_none(self):
        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("rating_pk", Operator.IN, [1, None])}),
            Projection("rating_pk", "rated_at", "rating", "book:author:birth_date"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "rating": 1,
                    "rated_at": datetime.datetime(2022, 12, 25, 10, 10, 10, tzinfo=datetime.timezone.utc),
                    "book": {"author": {"birth_date": datetime.date(1920, 2, 1)}},
                },
            ],
        )

        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeBranch(
                        "and",
                        [
                            ConditionTreeLeaf("rating_pk", Operator.IN, [1, 2]),
                            ConditionTreeLeaf("rating_pk", Operator.NOT_IN, [2, None]),
                        ],
                    )
                }
            ),
            Projection("rating_pk", "rated_at", "rating", "book:author:birth_date"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "rating": 1,
                    "rated_at": datetime.datetime(2022, 12, 25, 10, 10, 10, tzinfo=datetime.timezone.utc),
                    "book": {"author": {"birth_date": datetime.date(1920, 2, 1)}},
                },
            ],
        )


class TestDjangoCollectionCRUDListPolymorphism(TestDjangoCollectionCRUDList):
    def setUp(self) -> None:
        self.book_collection = DjangoCollection(self.datasource, Book, True)
        self.person_collection = DjangoCollection(self.datasource, Person, True)
        self.rating_collection = DjangoCollection(self.datasource, Rating, True)
        self.tag_collection = DjangoCollection(self.datasource, Tag, True)

    async def test_should_correctly_serialized_polymorphic_relation(self):
        """which mean all columns and no relations"""
        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeLeaf("rating_pk", "in", [1, 2]),
                    "page": Page(skip=0, limit=10),
                    "sort": Sort([{"field": "rating_pk", "ascending": True}]),
                }
            ),
            Projection("rating_pk", "content_object:*"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "content_object": {
                        "person_pk": 1,
                        "first_name": "Isaac",
                        "last_name": "Asimov",
                        "birth_date": datetime.date(1920, 2, 1),
                        "auth_user_id": None,
                    },
                },
                {
                    "rating_pk": 2,
                    "content_object": {"book_pk": 1, "name": "Foundation", "author_id": 1, "price": 1.23},
                },
            ],
        )

    async def test_should_correctly_replace_content_type_relation_by_str(self):
        """which mean all columns and no relations"""
        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeLeaf("rating_pk", "in", [1, 2]),
                    "page": Page(skip=0, limit=10),
                    "sort": Sort([{"field": "rating_pk", "ascending": True}]),
                }
            ),
            Projection("rating_pk", "content_type", "content_id"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "content_type": "test_app_person",
                    "content_id": 1,
                },
                {
                    "rating_pk": 2,
                    "content_type": "test_app_book",
                    "content_id": 1,
                },
            ],
        )

    async def test_should_correctly_handle_content_type_as_str_in_condition_tree(self):
        ret = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeLeaf("content_type", "equal", "test_app_person"),
                    "page": Page(skip=0, limit=10),
                    "sort": Sort([{"field": "rating_pk", "ascending": True}]),
                }
            ),
            Projection("rating_pk", "content_type", "content_id"),
        )

        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": 1,
                    "content_type": "test_app_person",
                    "content_id": 1,
                }
            ],
        )

    async def test_should_correctly_serialized_list_polymorphic_one_to_one(self):
        ret = await self.book_collection.list(
            self.mocked_caller,
            PaginatedFilter({"sort": Sort([{"field": "book_pk", "ascending": True}])}),
            Projection("book_pk", "tag:tag"),
        )

        self.assertEqual(
            ret,
            [
                {"book_pk": 1, "tag": {"tag": "best book"}},
                {"book_pk": 2, "tag": None},
                {"book_pk": 3, "tag": None},
            ],
        )


class TestDjangoCollectionCRUDAggregateBase(TestCase):
    fixtures = ["person.json", "book.json", "rating.json"]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.datasource = DjangoDatasource()

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
        self.book_collection = DjangoCollection(self.datasource, Book, False)
        self.person_collection = DjangoCollection(self.datasource, Person, False)
        self.rating_collection = DjangoCollection(self.datasource, Rating, False)


class TestDjangoCollectionCRUDAggregateNoGroupNoAggregateField(TestDjangoCollectionCRUDAggregateBase):
    async def test_aggregate_should_work(self):
        """typically the count http request"""
        ret = await self.book_collection.aggregate(self.mocked_caller, Filter({}), Aggregation({"operation": "Count"}))
        self.assertEqual(ret, [{"value": 3, "group": {}}])

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

    async def test_should_work_by_quarter(self):
        ret = await self.rating_collection.aggregate(
            self.mocked_caller,
            Filter({}),
            Aggregation(
                {
                    "operation": "Sum",
                    "field": "rating",
                    "groups": [{"field": "rated_at", "operation": DateOperation.QUARTER}],
                }
            ),
        )
        self.assertIn({"value": 16, "group": {"rated_at": datetime.date(2023, 3, 31)}}, ret)
        self.assertIn({"value": 1, "group": {"rated_at": datetime.date(2022, 12, 31)}}, ret)

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
                    "person_pk": ret[0]["person_pk"],
                    "auth_user_id": None,
                }
            ],
        )

        retrieved = await self.person_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("person_pk", Operator.EQUAL, ret[0]["person_pk"])}),
            Projection("person_pk", "first_name", "last_name", "birth_date", "auth_user_id"),
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
            Projection("person_pk", "first_name", "last_name", "birth_date"),
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
            Projection("person_pk", "last_name", "first_name"),
        )

        self.assertEqual(len(tolkiens), 4)


class TestDjangoCollectionCRUDCreateUpdateDeletePolymorphism(TestDjangoCollectionCRUDCreateUpdateDelete):
    def setUp(self) -> None:
        self.book_collection = DjangoCollection(self.datasource, Book, True)
        self.person_collection = DjangoCollection(self.datasource, Person, True)
        self.rating_collection = DjangoCollection(self.datasource, Rating, True)

    async def test_create_polymorphic_many_to_one_should_work(self):
        ret = await self.rating_collection.create(
            self.mocked_caller,
            [
                {
                    "comment": "super comment",
                    "commenter_id": 1,
                    "book_id": 1,
                    "rating": 3,
                    "rated_at": "2024-01-01T10:10:10:000000+00:00",
                    "content_type": "test_app_book",
                    "content_id": 1,
                }
            ],
        )
        self.assertEqual(
            ret,
            [
                {
                    "rating_pk": ret[0]["rating_pk"],
                    "comment": "super comment",
                    "commenter_id": 1,
                    "book_id": 1,
                    "rating": 3,
                    "rated_at": datetime.datetime(2024, 1, 1, 10, 10, 10, tzinfo=datetime.timezone.utc),
                    "content_type_id": 1,
                    "content_type": "test_app_book",
                    "content_id": 1,
                }
            ],
        )

        retrieved = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter({"condition_tree": ConditionTreeLeaf("rating_pk", Operator.EQUAL, ret[0]["rating_pk"])}),
            Projection("rating_pk", "comment", "rating", "rated_at", "content_object:*"),
        )
        self.assertEqual(
            retrieved,
            [
                {
                    "rating_pk": ret[0]["rating_pk"],
                    "comment": ret[0]["comment"],
                    "rating": ret[0]["rating"],
                    "rated_at": ret[0]["rated_at"],
                    "content_object": {"book_pk": 1, "name": "Foundation", "author_id": 1, "price": 1.23},
                },
            ],
        )

    async def test_update_polymorphic_many_to_one_should_work(self):
        records_before = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeBranch(
                        "and",
                        [
                            ConditionTreeLeaf("content_id", "equal", 1),
                            ConditionTreeLeaf("content_type", "equal", "test_app_person"),
                        ],
                    )
                }
            ),
            Projection("rating_pk", "content_type", "content_id", "content_object:*"),
        )
        # set to None
        await self.rating_collection.update(
            self.mocked_caller,
            Filter(
                {
                    "condition_tree": ConditionTreeBranch(
                        "and",
                        [
                            ConditionTreeLeaf("content_id", "equal", 1),
                            ConditionTreeLeaf("content_type", "equal", "test_app_person"),
                        ],
                    )
                },
            ),
            {
                "content_type": None,
                "content_id": None,
            },
        )

        # set to old value
        await self.rating_collection.update(
            self.mocked_caller,
            Filter(
                {
                    "condition_tree": ConditionTreeBranch(
                        "and",
                        [
                            ConditionTreeLeaf("content_id", "equal", None),
                            ConditionTreeLeaf("content_type", "equal", None),
                        ],
                    )
                },
            ),
            {
                "content_type": "test_app_person",
                "content_id": 1,
            },
        )
        # compare records
        records_after = await self.rating_collection.list(
            self.mocked_caller,
            PaginatedFilter(
                {
                    "condition_tree": ConditionTreeBranch(
                        "and",
                        [
                            ConditionTreeLeaf("content_id", "equal", 1),
                            ConditionTreeLeaf("content_type", "equal", "test_app_person"),
                        ],
                    )
                }
            ),
            Projection("rating_pk", "content_type", "content_id", "content_object:*"),
        )
        self.assertEqual(records_before, records_after)


class TestDjangoCollectionNativeDriver(TestDjangoCollectionCRUDAggregateBase):
    databases = "__all__"

    def test_native_driver_should_work(self):
        with self.book_collection.get_native_driver() as cursor:
            cursor.execute("select book_pk, name, author_id from test_app_book where book_pk=1")
            row = cursor.fetchone()

        self.assertEqual(row, (1, "Foundation", 1))

    def test_native_driver_should_work_and_restore_django_async_safe_variable(self):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "false"
        with self.book_collection.get_native_driver() as cursor:
            cursor.execute("select book_pk, name, author_id from test_app_book where book_pk=1")
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
