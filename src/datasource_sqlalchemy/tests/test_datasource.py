from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from tests.fixture import models


class TestSqlAlchemyDatasource(TestCase):
    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_create_datasource(self, mocked_sessionmaker):
        base_mock = Mock()
        with patch.object(SqlAlchemyDatasource, "_create_collections"):
            datasource = SqlAlchemyDatasource(base_mock)

            datasource._create_collections.assert_called()
        assert datasource._base == base_mock
        mocked_sessionmaker.assert_called()

    @patch("forestadmin.datasource_sqlalchemy.datasource.sessionmaker")
    def test_build_mapper(self, mocked_sessionmaker):
        base_mock = MagicMock()
        mocked_address = {
            "address": Mock(),
            "customer": Mock(),
            "customers_addresses": Mock(),
            "order": Mock(),
        }
        for k, v in mocked_address.items():
            v.persist_selectable.name = k
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
        base_mock = MagicMock()
        mocked_address = {
            "address": Mock(),
            "customer": Mock(),
            "customers_addresses": Mock(),
            "order": Mock(),
        }
        for k, v in mocked_address.items():
            v.name = k
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
