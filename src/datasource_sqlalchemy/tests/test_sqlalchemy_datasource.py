import asyncio
import os
from unittest import TestCase
from unittest.mock import Mock, patch

from flask import Flask
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyDatasourceException
from sqlalchemy.orm import DeclarativeMeta

from .fixture import models


class TestSqlAlchemyDatasource(TestCase):
    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_create_datasources_with_bind_in(self, mocked_sessionmaker):
        base_mock = Mock(DeclarativeMeta)
        base_mock.metadata = Mock()
        base_mock.metadata.bind.engine = "fake_bind"
        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)

            datasource._create_collections.assert_called()
        assert datasource._base == base_mock
        mocked_sessionmaker.assert_called()

    def test_create_datasources_should_raise_when_engine_not_found(self):
        base_mock = Mock(DeclarativeMeta)
        base_mock.metadata = Mock()
        base_mock.metadata.bind = None

        self.assertRaisesRegex(
            SqlAlchemyDatasourceException,
            r"Cannot find database uri in your SQLAlchemy Base class. You can pass it as a param:"
            + r" SqlAlchemyDatasource\(..., db_uri='sqlite:\/\/\/path\/to\/db.sql'\).",
            SqlAlchemyDatasource,
            base_mock,
        )

    def test_create_datasources_not_search_engine_when_db_uri_is_supply(self):
        base_mock = Mock(DeclarativeMeta)
        base_mock.metadata = Mock()
        base_mock.metadata.bind = None

        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            with patch.object(SqlAlchemyDatasource, "_find_db_uri") as mock_find_db_uri:
                datasource = SqlAlchemyDatasource(base_mock, db_uri="sqlite:///memory")
                mock_find_db_uri.assert_not_called()
                self.assertIsNotNone(datasource.Session)
            datasource._create_collections.assert_called()

    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_create_datasource_with_flask_sqlalchemy_integration_should_find_engine(self, mocked_sessionmaker):
        from flask_sqlalchemy import SQLAlchemy

        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///memory"
        db = SQLAlchemy()
        with app.app_context():
            db.init_app(app)

            with patch.object(SqlAlchemyDatasource, "_create_collections"):
                datasource = SqlAlchemyDatasource(db)
                datasource._create_collections.assert_called()

        assert datasource._base == db.Model

    @patch("forestadmin.datasource_sqlalchemy.datasource.SqlAlchemyCollection")
    def test_create_collection(self, mockSqlalchemyCollection):
        base_mock = Mock(DeclarativeMeta)
        base_mock.metadata = Mock()
        base_mock.metadata.bind = "fake_bind"
        mocked_address = {
            "address": Mock(),
            "customer": Mock(),
            "customers_addresses": Mock(),
            "order": Mock(),
        }
        for k, v in mocked_address.items():
            v.name = k
            v.persist_selectable.name = k
        base_mock.metadata = Mock()
        base_mock.metadata.sorted_tables = [v for k, v in mocked_address.items()]
        base_mock.registry = Mock()
        base_mock.registry.mappers = [v for k, v in mocked_address.items()]

        with patch.object(SqlAlchemyDatasource, "add_collection"):
            datasource = SqlAlchemyDatasource(base_mock)
            assert datasource.add_collection.call_count == 4
        mockSqlalchemyCollection.assert_called()


class TestSqlAlchemyDatasourceWithModels(TestCase):
    def test_with_models(self):
        datasource = SqlAlchemyDatasource(models.Base)

        assert len(datasource._collections) == 4
        assert datasource.get_collection("address").datasource == datasource


class TestSQLAlchemyDatasourceConnectionQueryCreation(TestCase):
    def test_should_not_create_native_query_connection_if_no_params(self):
        ds = SqlAlchemyDatasource(models.Base)
        self.assertEqual(ds.get_native_query_connections(), [])

    def test_should_create_native_query_connection_to_default_if_string_is_set(self):
        ds = SqlAlchemyDatasource(models.Base, live_query_connection="sqlalchemy")
        self.assertEqual(ds.get_native_query_connections(), ["sqlalchemy"])


class TestSQLAlchemyDatasourceNativeQueryExecution(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.loop = asyncio.new_event_loop()
        cls.sql_alchemy_base = models.get_models_base("test_datasource_native_query")
        if os.path.exists(cls.sql_alchemy_base.metadata.file_path):
            os.remove(cls.sql_alchemy_base.metadata.file_path)
        models.create_test_database(cls.sql_alchemy_base)
        models.load_fixtures(cls.sql_alchemy_base)
        cls.sql_alchemy_datasource = SqlAlchemyDatasource(models.Base, live_query_connection="sqlalchemy")

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.sql_alchemy_base.metadata.file_path)
        cls.loop.close()

    def test_should_raise_if_connection_is_not_known_by_datasource(self):
        self.assertRaisesRegex(
            SqlAlchemyDatasourceException,
            r"The native query connection 'foo' doesn't belongs to this datasource.",
            self.loop.run_until_complete,
            self.sql_alchemy_datasource.execute_native_query("foo", "select * from blabla", {}),
        )

    def test_should_correctly_execute_query(self):
        result = self.loop.run_until_complete(
            self.sql_alchemy_datasource.execute_native_query(
                "sqlalchemy", "select * from customer where id <= 2 order by id;", {}
            )
        )
        self.assertEqual(
            result,
            [
                {"id": 1, "first_name": "David", "last_name": "Myers", "age": 112},
                {"id": 2, "first_name": "Thomas", "last_name": "Odom", "age": 92},
            ],
        )

    def test_should_correctly_execute_query_with_formatting(self):
        result = self.loop.run_until_complete(
            self.sql_alchemy_datasource.execute_native_query(
                "sqlalchemy",
                """select *
                from customer
                where first_name = %(first_name)s
                    and last_name = %(last_name)s
                order by id""",
                {"first_name": "David", "last_name": "Myers"},
            )
        )
        self.assertEqual(
            result,
            [
                {"id": 1, "first_name": "David", "last_name": "Myers", "age": 112},
            ],
        )

    def test_should_correctly_execute_query_with_percent(self):
        result = self.loop.run_until_complete(
            self.sql_alchemy_datasource.execute_native_query(
                "sqlalchemy",
                """select *
                from customer
                where first_name like 'Dav\\%'
                order by id""",
                {},
            )
        )

        self.assertEqual(
            result,
            [
                {"id": 1, "first_name": "David", "last_name": "Myers", "age": 112},
            ],
        )

    def test_should_correctly_raise_exception_during_sql_error(self):
        self.assertRaisesRegex(
            SqlAlchemyDatasourceException,
            r"no such table: blabla",
            self.loop.run_until_complete,
            self.sql_alchemy_datasource.execute_native_query("sqlalchemy", "select * from blabla", {}),
        )
