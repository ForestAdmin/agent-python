import asyncio
import os
import sys
from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_sqlalchemy.collections import SqlAlchemyCollection, SqlAlchemyCollectionFactory
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyCollectionException
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import text

from .fixture import models


class TestSqlAlchemyCollection(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mocked_datasource = Mock()

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test_create(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()
        mocked_mapper = Mock()
        mocked_mapper.class_ = "model"

        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        assert mocked_sqlalchemy_collection_factory.called
        assert mocked_collection_factory.build.called

        assert collection.table == mocked_table
        assert collection.mapper == mocked_mapper
        assert collection.model == "model"
        assert collection.factory == collection._factory

        assert isinstance(collection._aliases, dict)

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test_create_no_mapper(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()

        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table)
        assert collection.model is None

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test_get_column(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()
        mocked_mapper = Mock()
        mocked_mapper.columns = {"city": "city_column"}
        mocked_mapper.class_ = "model"
        mocked_mapper.synonyms = []

        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        column = collection.get_column("city")
        assert column == "city_column"

        self.assertRaises(SqlAlchemyCollectionException, collection.get_column, "unknown_field")

        mocked_alias = Mock()
        del mocked_alias.synonyms
        mocked_alias.columns = {"city": "city_column"}
        column = collection.get_column("city", mocked_alias)
        assert column == "city_column"

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test__get_relationship(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()
        mocked_mapper = Mock()
        mocked_mapper.relationships = {"customers": "Customer"}
        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        relation = collection._get_relationship("customers")
        assert relation == "Customer"

        self.assertRaises(SqlAlchemyCollectionException, collection._get_relationship, "deliveries")

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test_get_columns(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()
        mocked_mapper = Mock()
        mocked_mapper.columns = {"city": "city_column", "zip_code": "zip_code_column"}
        mocked_mapper.synonyms = []
        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        with patch.object(SqlAlchemyCollection, "_get_related_column", return_value=([], {})):
            column, relation = collection.get_columns(Projection("city", "zip_code"))
        assert "city_column" in column
        assert "zip_code_column" in column
        assert len(relation) == 0

    @patch("forestadmin.datasource_sqlalchemy.collections.alias", return_value="alias_test")
    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test__get_alias(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory, mocked_sqlalchemy_alias):
        mocked_table = Mock()
        mocked_mapper = Mock()
        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        alias = collection._get_alias(mocked_mapper, "test")
        assert alias == "alias_test"
        assert mocked_sqlalchemy_alias.called

    @patch("forestadmin.datasource_sqlalchemy.collections.CollectionFactory")
    @patch("forestadmin.datasource_sqlalchemy.collections.SqlAlchemyCollectionFactory")
    def test__normalize_projection(self, mocked_sqlalchemy_collection_factory, mocked_collection_factory):
        mocked_table = Mock()
        mocked_mapper = Mock()
        mocked_mapper.columns = {"city": "city_column", "zip_code": "zip_code_column"}
        # mocked_mapper.relationships = {"customers": "Customer"}
        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        projection = collection._normalize_projection(Projection("city", "customers:first_name"))
        assert projection == Projection("city", "customers:first_name")


class BaseTestSqlAlchemyCollectionWithModels(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        cls.sql_alchemy_base = models.get_models_base("test_collection_operations")
        if os.path.exists(cls.sql_alchemy_base.metadata.file_path):
            os.remove(cls.sql_alchemy_base.metadata.file_path)
        models.create_test_database(cls.sql_alchemy_base)
        models.load_fixtures(cls.sql_alchemy_base)
        cls.datasource = SqlAlchemyDatasource(models.Base)
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

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.sql_alchemy_base.metadata.file_path)
        cls.loop.close()


class TestSqlAlchemyCollectionWithModels(BaseTestSqlAlchemyCollectionWithModels):
    def test_get_columns(self):
        collection = self.datasource.get_collection("order")
        columns, relationships = collection.get_columns(Projection("amount", "status", "customer:first_name"))

        assert len(columns) == 3
        assert len(relationships) == 1

        collection = self.datasource.get_collection("address")
        columns, relationships = collection.get_columns(Projection("city", "zip_code", "customers:first_name"))

        assert len(columns) == 3
        assert len(relationships) == 1

    def test_list(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 11)})
        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )

        assert len(results) == 10
        assert "id" in results[0]
        assert "created_at" in results[0]

    def test_list_with_filter(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 6)})

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        assert len(results) == 5

        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeLeaf(
                    "created_at",
                    Operator.AFTER,
                    "2023-01-01T00:00:00Z",
                )
            }
        )
        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        assert len(results) == 2

    def test_list_filter_in_and_not_in_with_null_in_values_should_work(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.IN, [1, None])})

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)

        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [ConditionTreeLeaf("id", Operator.IN, [1, 2]), ConditionTreeLeaf("id", Operator.NOT_IN, [2, None])],
                )
            }
        )

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 1)

    def test_list_filter_relation(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("customer:id", Operator.IN, [1, None])})

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "customer:id"))
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["customer"]["id"], 1)

    def test_list_with_filter_with_aggregator(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [ConditionTreeLeaf("id", Operator.LESS_THAN, 6), ConditionTreeLeaf("id", Operator.GREATER_THAN, 1)],
                ),
            }
        )

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        self.assertEqual(len(results), 4)

        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "or", [ConditionTreeLeaf("id", "equal", 6), ConditionTreeLeaf("id", "equal", 1)]
                ),
            }
        )
        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        self.assertEqual(len(results), 2)

    def test_list_should_handle_sort(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [ConditionTreeLeaf("id", Operator.LESS_THAN, 6), ConditionTreeLeaf("id", Operator.GREATER_THAN, 1)],
                ),
                "sort": [{"field": "id", "ascending": True}],
            }
        )

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        self.assertEqual(len(results), 4)
        for i in range(2, 6):
            self.assertEqual(results[i - 2]["id"], i)

        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [ConditionTreeLeaf("id", Operator.LESS_THAN, 6), ConditionTreeLeaf("id", Operator.GREATER_THAN, 1)],
                ),
                "sort": [{"field": "id", "ascending": False}],
            }
        )

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "created_at"))
        )
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["id"], 5)
        self.assertEqual(results[1]["id"], 4)
        self.assertEqual(results[2]["id"], 3)
        self.assertEqual(results[3]["id"], 2)

    def test_list_should_handle_multiple_sort(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [ConditionTreeLeaf("id", Operator.LESS_THAN, 6), ConditionTreeLeaf("id", Operator.GREATER_THAN, 1)],
                ),
                "sort": [
                    {"field": "status", "ascending": True},
                    {"field": "customer:id", "ascending": True},
                    {"field": "amount", "ascending": False},
                ],
            }
        )

        results = self.loop.run_until_complete(
            collection.list(self.mocked_caller, filter_, Projection("id", "customer:id", "status", "amount"))
        )
        self.assertEqual(len(results), 4)
        self.assertEqual(
            results,
            [
                {"id": 5, "status": models.ORDER_STATUS.DELIVERED, "amount": 9526, "customer": {"id": 8}},
                {"id": 3, "status": models.ORDER_STATUS.DELIVERED, "amount": 5285, "customer": {"id": 9}},
                {"id": 4, "status": models.ORDER_STATUS.DELIVERED, "amount": 4684, "customer": {"id": 9}},
                {"id": 2, "status": models.ORDER_STATUS.DELIVERED, "amount": 2664, "customer": {"id": 10}},
            ],
        )

    def test_create(self):
        order = {
            "id": 11,
            "created_at": datetime(2021, 5, 30, 1, 9, 31, tzinfo=zoneinfo.ZoneInfo(key="UTC")),
            "amount": 42,
            "customer_id": 6,
            "billing_address_id": 4,
            "delivering_address_id": 4,
            "status": "Rejected",
        }
        collection = self.datasource.get_collection("order")
        results = self.loop.run_until_complete(collection.create(self.mocked_caller, [order]))
        result = results[0]

        for field in order.keys():
            assert result[field] == order[field]

        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 11)})
        results = self.loop.run_until_complete(collection.list(self.mocked_caller, filter_, Projection(*order.keys())))
        result = results[0]

        for field in order.keys():
            assert result[field] == order[field]

    def test_create_error(self):
        order = {
            "id": 11,
            "created_at": datetime(2021, 5, 30, 1, 9, 31, tzinfo=zoneinfo.ZoneInfo(key="UTC")),
            # "amount": 42, # this field is mandatory
            "customer_id": 6,
            "billing_address_id": 4,
            "delivering_address_id": 4,
            "status": "Rejected",
        }
        collection = self.datasource.get_collection("order")
        self.assertRaises(
            SqlAlchemyCollectionException, self.loop.run_until_complete, collection.create(self.mocked_caller, [order])
        )

    def test_delete(self):
        order = {
            "id": 12,
            "created_at": datetime(2021, 5, 30, 1, 9, 31, tzinfo=zoneinfo.ZoneInfo(key="UTC")),
            "amount": 99,
            "customer_id": 9,
            "billing_address_id": 9,
            "delivering_address_id": 9,
            "status": "Rejected",
        }
        collection = self.datasource.get_collection("order")
        results = self.loop.run_until_complete(collection.create(self.mocked_caller, [order]))

        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 12)})
        results = self.loop.run_until_complete(collection.list(self.mocked_caller, filter_, Projection("id")))
        assert len(results) == 1

        self.loop.run_until_complete(collection.delete(self.mocked_caller, filter_))
        results = self.loop.run_until_complete(collection.list(self.mocked_caller, filter_, Projection("id")))

        assert len(results) == 0

    def test_update(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 10)})
        patch = {"amount": 42}
        collection = self.datasource.get_collection("order")
        self.loop.run_until_complete(collection.update(self.mocked_caller, filter_, patch))

        results = self.loop.run_until_complete(collection.list(self.mocked_caller, filter_, Projection("id", "amount")))
        assert results[0]["amount"] == 42

    def test_aggregate(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 11)})
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation({"operation": "Avg", "field": "amount", "groups": [{"field": "customer_id"}]}),
            )
        )

        assert len(results) == 7
        assert [*filter(lambda item: item["group"]["customer_id"] == 1, results)][0]["value"] == 5354.0
        assert [*filter(lambda item: item["group"]["customer_id"] == 2, results)][0]["value"] == 1031.0
        assert [*filter(lambda item: item["group"]["customer_id"] == 3, results)][0]["value"] == 9744.0
        assert [*filter(lambda item: item["group"]["customer_id"] == 4, results)][0]["value"] == 7676.0
        assert [*filter(lambda item: item["group"]["customer_id"] == 8, results)][0]["value"] == 4890.0
        assert [*filter(lambda item: item["group"]["customer_id"] == 9, results)][0]["value"] == 4984.5
        assert [*filter(lambda item: item["group"]["customer_id"] == 10, results)][0]["value"] == 3408.5

    def test_aggregate_by_date_year(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 11)})
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation(
                    {
                        "operation": "Avg",
                        "field": "amount",
                        "groups": [{"field": "created_at", "operation": "Year"}],
                    }
                ),
            )
        )

        self.assertEqual(len(results), 3)
        self.assertIn({"value": 5881.666666666667, "group": {"created_at": "2022-01-01"}}, results)
        self.assertIn({"value": 5278.5, "group": {"created_at": "2023-01-01"}}, results)
        self.assertIn({"value": 4433.8, "group": {"created_at": "2021-01-01"}}, results)

    def test_aggregate_by_date_quarter(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 11)})
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation(
                    {
                        "operation": "Avg",
                        "field": "amount",
                        "groups": [{"field": "created_at", "operation": "Quarter"}],
                    }
                ),
            )
        )

        self.assertEqual(len(results), 7)
        self.assertIn({"value": 9744.0, "group": {"created_at": "2021-09-30"}}, results)
        self.assertIn({"value": 7676.0, "group": {"created_at": "2022-09-30"}}, results)
        self.assertIn({"value": 5285.0, "group": {"created_at": "2022-06-30"}}, results)
        self.assertIn({"value": 5278.5, "group": {"created_at": "2023-03-31"}}, results)
        self.assertIn({"value": 4753.5, "group": {"created_at": "2021-03-31"}}, results)
        self.assertIn({"value": 4684.0, "group": {"created_at": "2022-12-31"}}, results)
        self.assertIn({"value": 1459.0, "group": {"created_at": "2021-06-30"}}, results)

    def test_aggregate_by_date_month(self):
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [
                        ConditionTreeLeaf("id", Operator.LESS_THAN, 11),
                        ConditionTreeLeaf("id", Operator.GREATER_THAN, 4),
                    ],
                )
            }
        )
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation(
                    {
                        "operation": "Avg",
                        "field": "amount",
                        "groups": [{"field": "created_at", "operation": "Month"}],
                    }
                ),
            )
        )

        self.assertEqual(len(results), 6)
        self.assertIn({"value": 9744.0, "group": {"created_at": "2021-07-01"}}, results)
        self.assertIn({"value": 9526.0, "group": {"created_at": "2023-02-01"}}, results)
        self.assertIn({"value": 7676.0, "group": {"created_at": "2022-08-01"}}, results)
        self.assertIn({"value": 5354.0, "group": {"created_at": "2021-01-01"}}, results)
        self.assertIn({"value": 4153.0, "group": {"created_at": "2021-03-01"}}, results)
        self.assertIn({"value": 254.0, "group": {"created_at": "2021-05-01"}}, results)

    def test_aggregate_by_date_week(self):
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [
                        ConditionTreeLeaf("id", Operator.LESS_THAN, 11),
                        ConditionTreeLeaf("id", Operator.GREATER_THAN, 4),
                    ],
                )
            }
        )
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation(
                    {
                        "operation": "Avg",
                        "field": "amount",
                        "groups": [{"field": "created_at", "operation": "Week"}],
                    }
                ),
            )
        )

        self.assertEqual(len(results), 6)
        self.assertIn({"value": 9744.0, "group": {"created_at": "2021-06-28"}}, results)
        self.assertIn({"value": 9526.0, "group": {"created_at": "2023-02-20"}}, results)
        self.assertIn({"value": 7676.0, "group": {"created_at": "2022-08-01"}}, results)
        self.assertIn({"value": 5354.0, "group": {"created_at": "2021-01-11"}}, results)
        self.assertIn({"value": 4153.0, "group": {"created_at": "2021-03-08"}}, results)
        self.assertIn({"value": 254.0, "group": {"created_at": "2021-05-24"}}, results)

    def test_aggregate_by_date_day(self):
        filter_ = PaginatedFilter(
            {
                "condition_tree": ConditionTreeBranch(
                    "and",
                    [
                        ConditionTreeLeaf("id", Operator.LESS_THAN, 11),
                        ConditionTreeLeaf("id", Operator.GREATER_THAN, 4),
                    ],
                )
            }
        )
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                self.mocked_caller,
                filter_,
                Aggregation(
                    {
                        "operation": "Avg",
                        "field": "amount",
                        "groups": [{"field": "created_at", "operation": "Day"}],
                    }
                ),
            )
        )

        self.assertEqual(len(results), 6)
        self.assertIn({"value": 9744.0, "group": {"created_at": "2021-07-05"}}, results)
        self.assertIn({"value": 9526.0, "group": {"created_at": "2023-02-27"}}, results)
        self.assertIn({"value": 7676.0, "group": {"created_at": "2022-08-07"}}, results)
        self.assertIn({"value": 5354.0, "group": {"created_at": "2021-01-13"}}, results)
        self.assertIn({"value": 4153.0, "group": {"created_at": "2021-03-13"}}, results)
        self.assertIn({"value": 254.0, "group": {"created_at": "2021-05-30"}}, results)

    def test_get_native_driver_should_return_connection(self):
        with self.datasource.get_collection("order").get_native_driver() as connection:
            self.assertIsInstance(connection, Session)
            self.assertEqual(str(connection.bind.url), f"sqlite:///{self.sql_alchemy_base.metadata.file_path}")

            rows = connection.execute(text('select id,amount from "order"  where id =  3')).all()
        self.assertEqual(rows, [(3, 5285)])

    def test_get_native_driver_should_work_without_declaring_request_as_text(self):
        with self.datasource.get_collection("order").get_native_driver() as connection:
            self.assertIsInstance(connection, Session)
            self.assertEqual(str(connection.bind.url), f"sqlite:///{self.sql_alchemy_base.metadata.file_path}")

            rows = connection.execute('select id,amount from "order"  where id =  3').all()
        self.assertEqual(rows, [(3, 5285)])


class TestSQLAlchemyOnSQLite(BaseTestSqlAlchemyCollectionWithModels):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dialect = "sqlite"

    def test_can_aggregate_date_by_year(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Year"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'strftime(:strftime_1, "order".created_at) AS created_at__grouped__ \n'
                'FROM "order" GROUP BY strftime(:strftime_1, "order".created_at) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-01-01"],
            )

    def test_can_aggregate_date_by_quarter(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Quarter"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date(strftime(:strftime_1, "order".created_at) || '
                ':strftime_2 || printf(:printf_1, (floor((CAST(strftime(:strftime_3, "order".created_at) AS INTEGER) '
                "- :param_1) / CAST(:param_2 AS NUMERIC)) + :floor_1) * :param_3) || :param_4, :date_1, :date_2) "
                "AS created_at__grouped__ \n"
                'FROM "order" GROUP BY date(strftime(:strftime_1, "order".created_at) || :strftime_2 || '
                'printf(:printf_1, (floor((CAST(strftime(:strftime_3, "order".created_at) AS INTEGER) - :param_1) / '
                "CAST(:param_2 AS NUMERIC)) + :floor_1) * :param_3) || :param_4, :date_1, :date_2) "
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y", "-", "%02d", "%m", 1, 3, 1, 3, "-01", "+1 month", "-1 day"],
            )

    def test_can_aggregate_date_by_month(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Month"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, strftime(:strftime_1, "order".created_at) '
                "AS created_at__grouped__ \n"
                'FROM "order" GROUP BY strftime(:strftime_1, "order".created_at) ORDER BY __aggregate__ DESC',
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-%m-01"],
            )

    def test_can_aggregate_date_by_week(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Week"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, DATE("order".created_at, :DATE_1, :DATE_2) AS '
                'created_at__grouped__ \nFROM "order" '
                'GROUP BY DATE("order".created_at, :DATE_1, :DATE_2) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["weekday 1", "-7 days"],
            )

    def test_can_aggregate_date_by_day(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Day"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, strftime(:strftime_1, "order".created_at) '
                "AS created_at__grouped__ \n"
                'FROM "order" GROUP BY strftime(:strftime_1, "order".created_at) ORDER BY __aggregate__ DESC',
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-%m-%d"],
            )


class TestSQLAlchemyOnPostgres(BaseTestSqlAlchemyCollectionWithModels):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dialect = "postgresql"

    def test_can_aggregate_date_by_year(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Year"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_trunc(:date_trunc_1, "order".created_at) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_trunc(:date_trunc_1, "order".created_at) ORDER BY __aggregate__ DESC NULLS LAST',
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["year"],
            )

    def test_can_aggregate_date_by_quarter(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Quarter"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_trunc(:date_trunc_1, "order".created_at) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_trunc(:date_trunc_1, "order".created_at) ORDER BY __aggregate__ DESC NULLS LAST',
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["quarter"],
            )

    def test_can_aggregate_date_by_month(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Month"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_trunc(:date_trunc_1, "order".created_at) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_trunc(:date_trunc_1, "order".created_at) ORDER BY __aggregate__ DESC NULLS LAST',
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["month"],
            )

    def test_can_aggregate_date_by_week(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Week"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_trunc(:date_trunc_1, "order".created_at) AS '
                "created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_trunc(:date_trunc_1, "order".created_at) '
                "ORDER BY __aggregate__ DESC NULLS LAST",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["week"],
            )

    def test_can_aggregate_date_by_day(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Day"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_trunc(:date_trunc_1, "order".created_at) AS '
                "created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_trunc(:date_trunc_1, "order".created_at) '
                "ORDER BY __aggregate__ DESC NULLS LAST",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["day"],
            )


class TestSQLAlchemyOnMySQL(BaseTestSqlAlchemyCollectionWithModels):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dialect = "mysql"  # same as 'mariadb'

    def test_can_aggregate_date_by_year(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Year"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_format("order".created_at, :date_format_1) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_format("order".created_at, :date_format_1) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-01-01"],
            )

    def test_can_aggregate_date_by_quarter(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Quarter"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, last_day(str_to_date(concat(year("order".created_at), '
                ':concat_1, lpad(ceiling(EXTRACT(month FROM "order".created_at) / CAST(:param_1 AS NUMERIC)'
                ") * :ceiling_1, :lpad_1, :lpad_2), :concat_2), :str_to_date_1)) AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY last_day(str_to_date(concat(year("order".created_at), :concat_1, '
                'lpad(ceiling(EXTRACT(month FROM "order".created_at) / CAST(:param_1 AS NUMERIC)'
                ") * :ceiling_1, :lpad_1, :lpad_2), :concat_2), :str_to_date_1)) "
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["-", 3, 3, 2, "0", "-01", "%Y-%m-%d"],
            )

    def test_can_aggregate_date_by_month(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Month"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_format("order".created_at, :date_format_1) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_format("order".created_at, :date_format_1) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-%m-01"],
            )

    def test_can_aggregate_date_by_week(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Week"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, CAST(date_sub("order".created_at, '
                "INTERVAL(WEEKDAY(order.created_at)) DAY) AS DATE) AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY CAST(date_sub("order".created_at, INTERVAL(WEEKDAY(order.created_at)) DAY) AS DATE) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                [],
            )

    def test_can_aggregate_date_by_day(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Day"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, date_format("order".created_at, :date_format_1) '
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY date_format("order".created_at, :date_format_1) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["%Y-%m-%d"],
            )


class TestSQLAlchemyOnMSSQL(BaseTestSqlAlchemyCollectionWithModels):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dialect = "mssql"

    def test_can_aggregate_date_by_year(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Year"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'datefromparts(EXTRACT(year FROM "order".created_at), '
                ":datefromparts_1, :datefromparts_2) "
                "AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY datefromparts(EXTRACT(year FROM "order".created_at), :datefromparts_1, :datefromparts_2) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["01", "01"],
            )

    def test_can_aggregate_date_by_quarter(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Quarter"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'eomonth(datefromparts(EXTRACT(YEAR FROM "order".created_at), '
                'datepart(QUARTER, "order".created_at) * 3, 1)) AS created_at__grouped__ \n'
                'FROM "order" '
                'GROUP BY eomonth(datefromparts(EXTRACT(YEAR FROM "order".created_at), '
                'datepart(QUARTER, "order".created_at) * 3, 1)) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                [],
            )

    def test_can_aggregate_date_by_month(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Month"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'datefromparts(EXTRACT(year FROM "order".created_at), EXTRACT(month FROM "order".created_at), '
                ":datefromparts_1) AS created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY datefromparts(EXTRACT(year FROM "order".created_at), EXTRACT(month FROM "order".created_at), '
                ":datefromparts_1) "
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                ["01"],
            )

    def test_can_aggregate_date_by_week(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Week"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'CAST(dateadd(day, -EXTRACT(dw FROM "order".created_at) + :param_1, "order".created_at) AS DATE) AS '
                "created_at__grouped__ \n"
                'FROM "order" '
                'GROUP BY CAST(dateadd(day, -EXTRACT(dw FROM "order".created_at) + :param_1, "order".created_at) '
                "AS DATE) "
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                [2],
            )

    def test_can_aggregate_date_by_day(self):
        with patch.object(self.datasource.Session, "begin") as mock_begin:
            mock_session = Mock()
            mock_session.execute = Mock(return_value=[])
            mock_session.bind.dialect.name = self.dialect
            mock_begin.return_value.__enter__.return_value = mock_session

            filter_ = PaginatedFilter({})
            collection = self.datasource.get_collection("order")
            self.loop.run_until_complete(
                collection.aggregate(
                    self.mocked_caller,
                    filter_,
                    Aggregation(
                        {
                            "operation": "Avg",
                            "field": "amount",
                            "groups": [{"field": "created_at", "operation": "Day"}],
                        }
                    ),
                )
            )
            query = mock_session.execute.call_args.args[0]
            sql_query = str(query)
            self.assertEqual(
                sql_query,
                'SELECT avg("order".amount) AS __aggregate__, '
                'datefromparts(EXTRACT(year FROM "order".created_at), EXTRACT(month FROM "order".created_at), '
                'EXTRACT(day FROM "order".created_at)) AS created_at__grouped__ \n'
                'FROM "order" '
                'GROUP BY datefromparts(EXTRACT(year FROM "order".created_at), EXTRACT(month FROM "order".created_at), '
                'EXTRACT(day FROM "order".created_at)) '
                "ORDER BY __aggregate__ DESC",
            )
            self.assertEqual(
                [p.value for p in query._get_embedded_bindparams()],
                [],
            )


class testSqlAlchemyCollectionFactory(TestCase):
    def test_create(self):
        mocked_collection = Mock()
        collection_factory = SqlAlchemyCollectionFactory(mocked_collection)
        assert collection_factory.collection == mocked_collection

    def test_init_instance(self):
        mocked_collection = Mock()
        mocked_collection.model = models.Address
        collection_factory = SqlAlchemyCollectionFactory(mocked_collection)
        data = {"id": 1, "street": "cadet", "city": "Paris", "country": "france", "zip_code": "75009"}
        model = collection_factory.init_instance(data)

        for field in data.keys():
            assert data[field] == getattr(model, field)

    def test_init_instance_err(self):
        mocked_collection = Mock()
        mocked_collection.model = None
        collection_factory = SqlAlchemyCollectionFactory(mocked_collection)

        self.assertRaises(Exception, collection_factory.init_instance, {})

    def test_init_instance_unknown_field(self):
        mocked_collection = Mock()

        def mocked_get_column(col_name):
            if col_name == "unknown_field":
                raise SqlAlchemyCollectionException()

        mocked_collection.get_column = mocked_get_column
        mocked_collection.model = models.Address
        collection_factory = SqlAlchemyCollectionFactory(mocked_collection)
        data = {
            "id": 1,
            "street": "cadet",
            "city": "Paris",
            "country": "france",
            "zip_code": "75009",
            "unknown_field": "unknown_value",
        }
        self.assertRaises(SqlAlchemyCollectionException, collection_factory.init_instance, data)

        data = {
            "id": None,
            "street": 12,
            "city": "Paris",
            "country": "france",
            "zip_code": "75009_",
        }
        self.assertRaises(TypeError, collection_factory.init_instance, data)

        data["zip_code"] = 75009
        model = collection_factory.init_instance(data)
        assert model.zip_code == "75009"
