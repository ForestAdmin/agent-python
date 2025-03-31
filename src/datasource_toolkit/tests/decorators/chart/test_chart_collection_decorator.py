import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection, CollectionException
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.chart_collection_decorator import ChartCollectionDecorator
from forestadmin.datasource_toolkit.decorators.chart.chart_datasource_decorator import ChartDataSourceDecorator
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType


class TestChartCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_product = Collection("Product", cls.datasource)
        cls.collection_product.add_fields(
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": [Operator.EQUAL, Operator.IN],
                },
            }
        )
        cls.datasource.add_collection(cls.collection_product)

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
        self.decorated_datasource = ChartDataSourceDecorator(self.datasource)
        self.decorated_collection: ChartCollectionDecorator = self.decorated_datasource.get_collection("Product")

    def test_schema_should_not_change(self):
        assert self.decorated_collection.schema["charts"] == self.collection_product.schema["charts"]

    def test_add_chart_should_raise_if_chart_name_already_exists(self):
        self.decorated_collection.add_chart("test_chart", lambda ctx, result_builder: True)
        self.assertRaisesRegex(
            CollectionException,
            r"🌳🌳🌳Chart test_chart already exists.",
            self.decorated_collection.add_chart,
            "test_chart",
            lambda ctx, result_builder: True,
        )

    def test_render_chart_should_call_child_collection(self):
        with patch.object(self.collection_product, "render_chart", new_callable=AsyncMock) as mock_render_chart:
            self.loop.run_until_complete(self.decorated_collection.render_chart(self.mocked_caller, "child_chart", [1]))

            mock_render_chart.assert_awaited_once_with(self.mocked_caller, "child_chart", [1])

    def test_chart_definition_should_be_called(self):
        async def chart_fn(context, result_builder: ResultBuilder, record_id):
            return result_builder.value(1)

        self.decorated_collection.add_chart("test_chart", chart_fn)
        result = self.loop.run_until_complete(
            self.decorated_collection.render_chart(self.mocked_caller, "test_chart", [1])
        )

        assert result == {"countCurrent": 1, "countPrevious": None}

    def test_should_schema_should_contains_charts_define_in_custom_datasource(self):
        with patch.dict(self.collection_product._schema, {"charts": {"chart_test": None}}):
            self.assertIn(
                "chart_test",
                self.decorated_collection.schema["charts"],
            )
