import asyncio
import sys
from unittest import TestCase
from unittest.mock import patch

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
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestCollectionChartContext(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_book = Collection("Product", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id_1": {
                    "column_type": PrimitiveType.NUMBER,
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "filter_operators": [Operator.EQUAL, Operator.IN],
                },
                "id_2": {
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

        cls.datasource_decorator = ChartDataSourceDecorator(cls.datasource)

    def setUp(self) -> None:
        self.decorated_book_collection = self.datasource_decorator.get_collection("Product")

    def test_record_id_should_throw_an_error(self):
        collection_chart_context = CollectionChartContext(self.mocked_caller, self.decorated_book_collection, [1, 2])
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"Collection is using a composite pk: use 'context.composite_record_id'\.",
            self.loop.run_until_complete,
            collection_chart_context.get_record_id(),
        )

    def test_get_record_id_should_work(self):
        collection_chart_context = CollectionChartContext(self.mocked_caller, self.decorated_book_collection, [1])
        record_id = self.loop.run_until_complete(collection_chart_context.get_record_id())

        assert record_id == 1

    def test_composite_record_id_should_return_record_id(self):
        collection_chart_context = CollectionChartContext(self.mocked_caller, self.decorated_book_collection, [1, 2])
        record_id = collection_chart_context.composite_record_id
        assert record_id == [1, 2]

    def test_get_record_should_return_record(self):
        collection_chart_context = CollectionChartContext(self.mocked_caller, self.decorated_book_collection, [1, 2])

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id_1": 1, "id_2": 2}]):
            record = self.loop.run_until_complete(collection_chart_context.get_record(Projection("id_1", "id_2")))

        assert record == {"id_1": 1, "id_2": 2}
