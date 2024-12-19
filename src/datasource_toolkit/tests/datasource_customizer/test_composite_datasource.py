import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, NativeQueryException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType


class BaseTestCompositeDatasource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

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
        self.composite_ds = CompositeDatasource()
        self.ds1_charts = {"charts": {"chart1": Mock()}}
        self.ds2_charts = {"charts": {"chart2": Mock()}}

        self.ds1_connections = ["db1", "db2"]
        self.ds2_connections = ["db3"]

        DS1 = type(
            "DS1",
            (Datasource,),
            {
                "schema": PropertyMock(return_value=self.ds1_charts),
                "get_native_query_connections": Mock(return_value=self.ds1_connections),
            },
        )
        DS2 = type(
            "DS2",
            (Datasource,),
            {
                "schema": PropertyMock(return_value=self.ds2_charts),
                "get_native_query_connections": Mock(return_value=self.ds2_connections),
            },
        )

        self.datasource_1: Datasource = DS1()
        self.collection_person = Collection("Person", self.datasource_1)
        self.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )
        self.datasource_1.add_collection(self.collection_person)

        self.datasource_2: Datasource = DS2()
        self.collection_order = Collection("Order", self.datasource_2)
        self.collection_order.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "customer_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "price": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
            }
        )

        self.datasource_2.add_collection(self.collection_order)


class TestCompositeDatasource(BaseTestCompositeDatasource):
    def setUp(self) -> None:
        super().setUp()
        self.composite_ds.add_datasource(self.datasource_1)

    def test_add_datasource_should_raise_if_multiple_collection_with_same_name(self):
        collection_person = Collection("Person", self.datasource_2)
        collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
            }
        )
        self.datasource_2.add_collection(collection_person)

        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"Collection 'Person' already exists\.",
            self.composite_ds.add_datasource,
            self.datasource_2,
        )

    def test_collection_should_return_collection_of_all_datasources(self):
        self.composite_ds.add_datasource(self.datasource_2)

        self.assertEqual(len(self.composite_ds.collections), 2)
        self.assertIn("Person", [c.name for c in self.composite_ds.collections])
        self.assertIn("Order", [c.name for c in self.composite_ds.collections])

    def test_get_collection_should_search_in_all_datasources(self):
        self.composite_ds.add_datasource(self.datasource_2)

        collection = self.composite_ds.get_collection("Person")
        self.assertEqual(collection.name, "Person")
        self.assertEqual(collection.datasource, self.datasource_1)

        collection = self.composite_ds.get_collection("Order")
        self.assertEqual(collection.name, "Order")
        self.assertEqual(collection.datasource, self.datasource_2)

    def test_get_collection_should_list_collection_names_if_collection_not_found(self):
        self.composite_ds.add_datasource(self.datasource_2)

        self.assertRaisesRegex(
            DatasourceToolkitException,
            "Collection Unknown not found. List of available collection: Order, Person",
            self.composite_ds.get_collection,
            "Unknown",
        )


class TestCompositeDatasourceCharts(BaseTestCompositeDatasource):
    def setUp(self) -> None:
        self.ds1_charts = {"charts": {"chart1": Mock()}}
        self.ds2_charts = {"charts": {"chart2": Mock()}}
        super().setUp()

        self.composite_ds.add_datasource(self.datasource_1)

    def test_add_datasource_should_raise_if_duplicated_chart(self):
        self.ds1_charts["charts"]["chart2"] = Mock()

        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"Chart 'chart2' already exists.",
            self.composite_ds.add_datasource,
            self.datasource_2,
        )

    def test_schema_should_contains_all_charts(self):
        self.composite_ds.add_datasource(self.datasource_2)
        self.assertIn("chart1", self.composite_ds.schema["charts"])
        self.assertIn("chart2", self.composite_ds.schema["charts"])

    def test_render_chart_should_raise_if_chart_is_unknown(self):
        self.composite_ds.add_datasource(self.datasource_2)
        self.assertRaisesRegex(
            DatasourceToolkitException,
            "Chart unknown is not defined in the datasource.",
            self.loop.run_until_complete,
            self.composite_ds.render_chart(self.mocked_caller, "unknown"),
        )

    def test_render_chart_should_call_render_chart_on_good_datasource(self):
        self.composite_ds.add_datasource(self.datasource_2)

        with patch.object(self.datasource_1, "render_chart", new_callable=AsyncMock) as mock_render_chart:
            self.loop.run_until_complete(self.composite_ds.render_chart(self.mocked_caller, "chart1"))
            mock_render_chart.assert_awaited_with(self.mocked_caller, "chart1")

        with patch.object(self.datasource_2, "render_chart", new_callable=AsyncMock) as mock_render_chart:
            self.loop.run_until_complete(self.composite_ds.render_chart(self.mocked_caller, "chart2"))
            mock_render_chart.assert_awaited_with(self.mocked_caller, "chart2")


class TestCompositeDatasourceNativeQuery(BaseTestCompositeDatasource):

    def setUp(self) -> None:
        super().setUp()
        self.composite_ds.add_datasource(self.datasource_1)

    def test_add_datasource_should_raise_if_duplicated_live_query_connection(self):
        with patch.object(self.datasource_2, "get_native_query_connections", return_value=["db1"]):
            self.assertRaisesRegex(
                DatasourceToolkitException,
                r"Native query connection 'db1' already exists.",
                self.composite_ds.add_datasource,
                self.datasource_2,
            )

    def test_get_native_query_connection_should_return_all_connections(self):
        self.composite_ds.add_datasource(self.datasource_2)
        connections = self.composite_ds.get_native_query_connections()
        self.assertIn("db1", connections)
        self.assertIn("db2", connections)
        self.assertIn("db3", connections)

    def test_execute_native_query_should_raise_if_connection_is_unknown(self):
        self.composite_ds.add_datasource(self.datasource_2)

        self.assertRaisesRegex(
            NativeQueryException,
            r"Native query connection 'bla' is unknown",
            self.loop.run_until_complete,
            self.composite_ds.execute_native_query("bla", "select * from ...", {}),
        )

    def test_execute_native_query_should_call_to_correct_datasource(self):
        self.composite_ds.add_datasource(self.datasource_2)

        with patch.object(self.datasource_1, "execute_native_query", new_callable=AsyncMock) as mock_ds1_exec:
            self.loop.run_until_complete(self.composite_ds.execute_native_query("db1", "select * from ...", {}))
            mock_ds1_exec.assert_any_await("db1", "select * from ...", {})

            self.loop.run_until_complete(self.composite_ds.execute_native_query("db2", "select * from ...", {}))
            mock_ds1_exec.assert_any_await("db2", "select * from ...", {})

        with patch.object(self.datasource_2, "execute_native_query", new_callable=AsyncMock) as mock_ds2_exec:
            self.loop.run_until_complete(self.composite_ds.execute_native_query("db3", "select * from ...", {}))
            mock_ds2_exec.assert_any_await("db3", "select * from ...", {})
