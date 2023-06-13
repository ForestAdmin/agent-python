from unittest import TestCase
from unittest.mock import Mock, patch

from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyDatasourceException
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.sql.schema import MetaData
from tests.fixture import models


class TestSqlAlchemyDatasource(TestCase):
    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_create_datasource(self, mocked_sessionmaker):
        base_mock = Mock(DeclarativeMeta)
        base_mock.metadata = Mock()
        base_mock.metadata.bind = "fake_bind"
        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)

            datasource._create_collections.assert_called()
        assert datasource._base == base_mock
        mocked_sessionmaker.assert_called()

    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_create_datasource_flask_sqlalchemy(self, mocked_sessionmaker):
        base_mock = Mock()
        base_mock.metadata = Mock()
        base_mock.metadata.bind = "fake_bind"
        base_mock.Model = Mock()
        base_mock.Model.metadata = Mock(MetaData)

        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)

            datasource._create_collections.assert_called()
        assert datasource._base == base_mock.Model

        base_mock.metadata = Mock(MetaData)
        base_mock.metadata.bind = None
        base_mock.engine = {"fake_engine": True}

        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)

            datasource._create_collections.assert_called()
        assert datasource._base == base_mock.Model

    def test_create_datasource_error(self):
        base_mock = Mock()
        base_mock.Model = Mock()
        base_mock.Model.metadata = Mock()
        self.assertRaises(SqlAlchemyDatasourceException, SqlAlchemyDatasource, base_mock)

        base_mock.Model.metadata = Mock(MetaData)
        base_mock.metadata = Mock()
        base_mock.metadata.bind = None
        base_mock.engine = None
        self.assertRaises(SqlAlchemyDatasourceException, SqlAlchemyDatasource, base_mock)

    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_build_mapper(self, mocked_sessionmaker):
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
            v.persist_selectable.name = k
        base_mock.registry = Mock()
        base_mock.registry.mappers = [v for k, v in mocked_address.items()]

        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)
            mappers = datasource.build_mappers()

        assert len(mappers.keys()) == 4
        for name in mocked_address.keys():
            assert name in mappers.keys()
            assert mappers[name] == mocked_address[name]

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
        base_mock.metadata = Mock()
        base_mock.metadata.sorted_tables = [v for k, v in mocked_address.items()]
        with patch.object(SqlAlchemyDatasource, "add_collection"):
            with patch.object(
                SqlAlchemyDatasource,
                "build_mappers",
                return_value={
                    "address": Mock(),
                    "customer": Mock(),
                    "customers_addresses": Mock(),
                    "order": Mock(),
                },
            ):
                datasource = SqlAlchemyDatasource(base_mock)
            assert datasource.add_collection.call_count == 4
        mockSqlalchemyCollection.assert_called()


class TestSqlAlchemyDatasourceWithModels(TestCase):
    def test_with_models(self):
        datasource = SqlAlchemyDatasource(models.Base)

        assert len(datasource._collections) == 4
        assert datasource.get_collection("address").datasource == datasource
