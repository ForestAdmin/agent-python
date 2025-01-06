import asyncio
import sys
from logging import Filter
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.hook.collections import CollectionHookDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestHookCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        Collection.create = AsyncMock()
        Collection.update = AsyncMock()
        Collection.delete = AsyncMock()
        Collection.aggregate = AsyncMock()
        cls.collection_transaction = Collection("Transaction", cls.datasource)
        cls.collection_transaction.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "description": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "amount": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
            }
        )

        cls.datasource.add_collection(cls.collection_transaction)

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
        self.datasource_decorator = DatasourceDecorator(self.datasource, CollectionHookDecorator)

        self.decorated_collection_transaction = self.datasource_decorator.get_collection("Transaction")

    def test_schema_should_not_change(self):
        self.assertDictEqual(self.decorated_collection_transaction.schema, self.collection_transaction.schema)


class TestBeforeHookCollectionDecorator(TestHookCollectionDecorator):
    def test_list_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("Before", "List", hook)

        filter_ = PaginatedFilter({})
        projection = Projection()

        self.loop.run_until_complete(
            self.decorated_collection_transaction.list(self.mocked_caller, filter_, projection)
        )

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].projection, projection)

    def test_create_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("Before", "Create", hook)

        data = [{"description": "desc", "amount": 10}]

        self.loop.run_until_complete(self.decorated_collection_transaction.create(self.mocked_caller, data))

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].data, data)

    def test_update_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("Before", "Update", hook)

        patch = [{"amount": 0}]
        filter_ = Filter({})

        self.loop.run_until_complete(self.decorated_collection_transaction.update(self.mocked_caller, filter_, patch))

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].patch, patch)

    def test_delete_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("Before", "Delete", hook)

        filter_ = Filter({})

        self.loop.run_until_complete(self.decorated_collection_transaction.delete(self.mocked_caller, filter_))

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)

    def test_aggregate_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("Before", "Aggregate", hook)

        filter_ = Filter({})
        aggregation = Aggregation({"operation": "Count"})

        self.loop.run_until_complete(
            self.decorated_collection_transaction.aggregate(self.mocked_caller, filter_, aggregation)
        )

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].aggregation, aggregation)


class TestAfterHookCollectionDecorator(TestHookCollectionDecorator):
    def test_list_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("After", "List", hook)

        filter_ = PaginatedFilter({})
        projection = Projection()
        records = [{"id": 1, "description": "desc", "amount": 2}]

        with patch.object(
            self.collection_transaction, "list", new_callable=AsyncMock, return_value=records
        ) as mocked_list:
            self.loop.run_until_complete(
                self.decorated_collection_transaction.list(self.mocked_caller, filter_, projection)
            )
            mocked_list.assert_awaited_once()

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].projection, projection)
        self.assertEqual(args[0].records, records)

    def test_create_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("After", "Create", hook)

        data = [{"description": "desc", "amount": 10}]
        records = [{"id": 1, "description": "desc", "amount": 10}]

        with patch.object(
            self.collection_transaction, "create", new_callable=AsyncMock, return_value=records
        ) as mocked_create:
            self.loop.run_until_complete(self.decorated_collection_transaction.create(self.mocked_caller, data))
            mocked_create.assert_awaited_once()

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].data, data)
        self.assertEqual(args[0].records, records)

    def test_update_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("After", "Update", hook)

        patch_ = [{"amount": 0}]
        filter_ = Filter({})

        with patch.object(
            self.collection_transaction,
            "update",
            new_callable=AsyncMock,
        ) as mocked_update:
            self.loop.run_until_complete(
                self.decorated_collection_transaction.update(self.mocked_caller, filter_, patch_)
            )
            mocked_update.assert_awaited_once()

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].patch, patch_)

    def test_delete_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("After", "Delete", hook)

        filter_ = Filter({})

        with patch.object(
            self.collection_transaction,
            "delete",
            new_callable=AsyncMock,
        ) as mocked_delete:
            self.loop.run_until_complete(self.decorated_collection_transaction.delete(self.mocked_caller, filter_))
            mocked_delete.assert_awaited_once()

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)

    def test_aggregate_should_call_hook_with_valid_parameters(self):
        hook = Mock()
        self.decorated_collection_transaction.add_hook("After", "Aggregate", hook)

        filter_ = Filter({})
        aggregation = Aggregation({"operation": "Count"})
        aggregate_result = [{"value": 1, "group": {}}]

        with patch.object(
            self.collection_transaction, "aggregate", new_callable=AsyncMock, return_value=aggregate_result
        ) as mocked_aggregate:
            self.loop.run_until_complete(
                self.decorated_collection_transaction.aggregate(self.mocked_caller, filter_, aggregation)
            )
            mocked_aggregate.assert_awaited_once()

        hook.assert_called_once()
        args = hook.call_args_list[0][0]
        self.assertEqual(args[0].caller, self.mocked_caller)
        self.assertEqual(args[0].filter, filter_)
        self.assertEqual(args[0].aggregation, aggregation)
        self.assertEqual(args[0].aggregate_result, aggregate_result)
