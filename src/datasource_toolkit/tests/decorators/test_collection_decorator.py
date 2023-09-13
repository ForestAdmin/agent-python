import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_product = Collection("Product", cls.datasource)
        cls.collection_product.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "price": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_product)
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, CollectionDecorator)

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
        self.decorated_collection_product = self.datasource_decorator.get_collection("Product")

    def test_name_should_return_child_collection_name(self):
        assert self.decorated_collection_product.name == self.collection_product.name

    def test_schema_call_child_collection_schema(self):
        returned_schema = self.decorated_collection_product.schema

        assert returned_schema == self.collection_product.schema

    def test_get_fields_should_get_fields_from_schema(self):
        returned_schema = self.decorated_collection_product.schema

        assert returned_schema["fields"]["id"] == self.decorated_collection_product.get_field("id")
        assert returned_schema["fields"]["name"] == self.decorated_collection_product.get_field("name")
        assert returned_schema["fields"]["price"] == self.decorated_collection_product.get_field("price")

    def test_execute_should_call_child_collection_execute(self):
        with patch.object(self.collection_product, "execute", new_callable=AsyncMock) as mock_execute:
            self.loop.run_until_complete(self.decorated_collection_product.execute(self.mocked_caller, "foo", []))

            mock_execute.assert_awaited_once_with(self.mocked_caller, "foo", [], None)

    def test_get_form_should_call_child_collection_get_form(self):
        with patch.object(self.collection_product, "get_form", new_callable=AsyncMock) as mock_get_form:
            self.loop.run_until_complete(self.decorated_collection_product.get_form(self.mocked_caller, "foo", []))

            mock_get_form.assert_awaited_once_with(self.mocked_caller, "foo", [], None, {})

    def test_create_should_call_child_collection_create(self):
        with patch.object(self.collection_product, "create", new_callable=AsyncMock) as mock_create:
            self.loop.run_until_complete(self.decorated_collection_product.create(self.mocked_caller, []))

            mock_create.assert_awaited_once_with(self.mocked_caller, [])

    def test_list_should_call_child_collection_list(self):
        patched_records = [
            {"id": 1, "name": "foo1", "price": 1000},
            {"id": 2, "name": "foo2", "price": 1500},
            {"id": 3, "name": "foo3", "price": 2000},
        ]
        with patch.object(
            self.collection_product, "list", new_callable=AsyncMock, return_value=patched_records
        ) as mock_list:
            records = self.loop.run_until_complete(
                self.decorated_collection_product.list(
                    self.mocked_caller, Filter({}), Projection("id", "name", "price")
                )
            )

            mock_list.assert_awaited_once_with(self.mocked_caller, Filter({}), Projection("id", "name", "price"))

        assert records == patched_records

    def test_update_should_call_child_collection_update(self):
        with patch.object(self.collection_product, "update", new_callable=AsyncMock) as mock_update:
            self.loop.run_until_complete(
                self.decorated_collection_product.update(self.mocked_caller, Filter({}), {"id": 1})
            )

            mock_update.assert_awaited_once_with(self.mocked_caller, Filter({}), {"id": 1})

    def test_delete_should_call_child_collection_delete(self):
        with patch.object(self.collection_product, "delete", new_callable=AsyncMock) as mock_delete:
            self.loop.run_until_complete(self.decorated_collection_product.delete(self.mocked_caller, Filter({})))

            mock_delete.assert_awaited_once_with(self.mocked_caller, Filter({}))

    def test_aggregate_should_call_child_collection_aggregate(self):
        patched_aggregate_return = [{"group": {}, "value": 12}]
        with patch.object(
            self.collection_product, "aggregate", new_callable=AsyncMock, return_value=patched_aggregate_return
        ) as mock_aggregate:
            records = self.loop.run_until_complete(
                self.decorated_collection_product.aggregate(
                    self.mocked_caller, Filter({}), Aggregation({"operation": "Count"})
                )
            )

            mock_aggregate.assert_awaited_once_with(
                self.mocked_caller, Filter({}), Aggregation({"operation": "Count"}), None
            )

        assert records == patched_aggregate_return

    def test_refine_schema_must_return_given_schema(self):
        assert self.collection_product.schema == self.decorated_collection_product._refine_schema(
            self.collection_product.schema
        )

    def test_refine_filter_must_return_given_filter(self):
        assert (
            self.loop.run_until_complete(self.decorated_collection_product._refine_filter(self.mocked_caller, None))
            is None
        )
        assert self.loop.run_until_complete(
            self.decorated_collection_product._refine_filter(self.mocked_caller, Filter({}))
        ) == Filter({})
