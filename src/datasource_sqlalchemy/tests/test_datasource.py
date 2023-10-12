from unittest import TestCase
from unittest.mock import Mock, patch

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyDatasourceException
from sqlalchemy.orm import DeclarativeMeta
from tests.fixture import models


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
            + r" SqlAlchemyDatasource\(db_uri='sqlite:\/\/\/path\/to\/db.sql'\).",
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
        app = Flask(__name__)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///memory"
        db = SQLAlchemy()
        with app.app_context():
            db.init_app(app)

            with patch.object(SqlAlchemyDatasource, "_create_collections"):
                datasource = SqlAlchemyDatasource(db)
                datasource._create_collections.assert_called()

        assert datasource._base == db.Model

    # @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    # def test_build_mapper(self, mocked_sessionmaker):
    #     base_mock = Mock(DeclarativeMeta)
    #     base_mock.metadata = Mock()
    #     base_mock.metadata.bind = "fake_bind"
    #     mocked_address = {
    #         "address": Mock(),
    #         "customer": Mock(),
    #         "customers_addresses": Mock(),
    #         "order": Mock(),
    #     }
    #     for k, v in mocked_address.items():
    #         v.persist_selectable.name = k
    #     base_mock.registry = Mock()
    #     base_mock.registry.mappers = [v for k, v in mocked_address.items()]

    #     with patch.object(SqlAlchemyDatasource, "_create_collections"):
    #         datasource = SqlAlchemyDatasource(base_mock)
    #         mappers = datasource.build_mappers()

    #     assert len(mappers.keys()) == 4
    #     for name in mocked_address.keys():
    #         assert name in mappers.keys()
    #         assert mappers[name] == mocked_address[name]

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
