import asyncio
import os
import sys
from datetime import datetime
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_sqlalchemy.collections import SqlAlchemyCollection, SqlAlchemyCollectionFactory
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyCollectionException
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from tests.fixture import models


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

        with patch.object(SqlAlchemyCollection, "add_field"):
            collection = SqlAlchemyCollection("address", self.mocked_datasource, mocked_table, mocked_mapper)

        column = collection.get_column("city")
        assert column == "city_column"

        self.assertRaises(SqlAlchemyCollectionException, collection.get_column, "unknown_field")

        mocked_alias = Mock()
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


class TestSqlAlchemyCollectionWithModels(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loop = asyncio.new_event_loop()
        if os.path.exists(models.test_db_path):
            os.remove(models.test_db_path)
        models.create_test_database()
        models.load_fixtures()
        cls.datasource = SqlAlchemyDatasource(models.Base)

    @classmethod
    def tearDownClass(cls):
        os.remove(models.test_db_path)
        cls.loop.close()

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
        results = self.loop.run_until_complete(collection.list(filter_, Projection("id", "created_at")))

        assert len(results) == 10
        assert "id" in results[0]
        assert "created_at" in results[0]

    def test_list_with_filter(self):
        collection = self.datasource.get_collection("order")
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 6)})

        results = self.loop.run_until_complete(collection.list(filter_, Projection("id", "created_at")))
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
        results = self.loop.run_until_complete(collection.list(filter_, Projection("id", "created_at")))
        assert len(results) == 2

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
        results = self.loop.run_until_complete(collection.create([order]))
        result = results[0]

        for field in order.keys():
            assert result[field] == order[field]

        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 11)})
        results = self.loop.run_until_complete(collection.list(filter_, Projection(*order.keys())))
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
        self.assertRaises(SqlAlchemyCollectionException, self.loop.run_until_complete, collection.create([order]))

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
        results = self.loop.run_until_complete(collection.create([order]))

        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 12)})
        results = self.loop.run_until_complete(collection.list(filter_, Projection("id")))
        assert len(results) == 1

        self.loop.run_until_complete(collection.delete(filter_))
        results = self.loop.run_until_complete(collection.list(filter_, Projection("id")))

        assert len(results) == 0

    def test_update(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 10)})
        patch = {"amount": 42}
        collection = self.datasource.get_collection("order")
        self.loop.run_until_complete(collection.update(filter_, patch))

        results = self.loop.run_until_complete(collection.list(filter_, Projection("id", "amount")))
        assert results[0]["amount"] == 42

    def test_aggregate(self):
        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("id", Operator.LESS_THAN, 11)})
        collection = self.datasource.get_collection("order")

        results = self.loop.run_until_complete(
            collection.aggregate(
                filter_, Aggregation({"operation": "Avg", "field": "amount", "groups": [{"field": "customer_id"}]})
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
