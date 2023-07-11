import asyncio
import sys
from unittest import TestCase
from unittest.mock import PropertyMock, patch

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from mock import AsyncMock
if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.chart.chart_datasource_decorator import ChartDataSourceDecorator
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType


class TestChartDatasourceDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_book = Collection("Product", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": [Operator.EQUAL, Operator.IN],
                },
            }
        )
        cls.datasource.add_collection(cls.collection_book)

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
        self.decorated_datasource = ChartDataSourceDecorator(self.datasource)

    def test_schema_should_not_contains_charts(self):
        assert self.decorated_datasource.schema == self.datasource.schema
        assert self.decorated_datasource.schema["charts"] == {}

    def test_schema_should_contains_charts(self):
        async def chart_def(context, result_builder: ResultBuilder):
            return result_builder.value(42)

        self.decorated_datasource.add_chart("test_chart", chart_def)
        assert self.decorated_datasource.schema["charts"] == {"test_chart": chart_def}

    def test_add_chart_should_raise_if_chart_name_already_exists(self):
        self.decorated_datasource.add_chart("test_chart", lambda ctx, result_builder: True)
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Chart test_chart already exists.",
            self.decorated_datasource.add_chart,
            "test_chart",
            lambda ctx, result_builder: True,
        )

    def test_render_chart_should_call_chart_definition(self):
        async def chart_def(context, result_builder: ResultBuilder):
            return result_builder.value(42)

        self.decorated_datasource.add_chart("test_chart", chart_def)

        result = self.loop.run_until_complete(self.decorated_datasource.render_chart(self.mocked_caller, "test_chart"))
        assert result == {"countCurrent": 42, "countPrevious": None}

    def test_render_chart_should_call_child_datasource_render_chart_if_no_chart(self):
        with patch.object(self.datasource, "render_chart", new_callable=AsyncMock) as mock_render_chart:
            self.loop.run_until_complete(self.decorated_datasource.render_chart(self.mocked_caller, "test_chart"))

            mock_render_chart.assert_awaited_once_with(self.mocked_caller, "test_chart")

    def test_render_chart_should_call_parent_and_throw(self):
        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Chart test_chart not exists on this datasource",
            self.loop.run_until_complete,
            self.decorated_datasource.render_chart(self.mocked_caller, "test_chart"),
        )

    def test_add_chart_should_raise_when_adding_chart_already_existing_in_child_datasource(self):
        with patch(
            "forestadmin.datasource_toolkit.datasources.Datasource.schema",
            new_callable=PropertyMock,
            return_value={"charts": {"test_chart": lambda ctx, result_builder: True}},
        ):
            self.assertRaisesRegex(
                DatasourceToolkitException,
                "🌳🌳🌳Chart test_chart already exists.",
                self.decorated_datasource.add_chart,
                "test_chart",
                lambda ctx, result_builder: False,
            )

    def test_adding_two_charts_on_two_datasources_should_make_schema_raise(self):
        datasource = Datasource()
        chart_datasource_1 = ChartDataSourceDecorator(datasource)
        chart_datasource_2 = ChartDataSourceDecorator(chart_datasource_1)

        chart_datasource_2.add_chart("test_chart", lambda ctx, result_builder: True)
        chart_datasource_1.add_chart("test_chart", lambda ctx, result_builder: True)

        with self.assertRaisesRegex(DatasourceToolkitException, "🌳🌳🌳Chart test_chart is defined twice."):
            chart_datasource_2.schema
