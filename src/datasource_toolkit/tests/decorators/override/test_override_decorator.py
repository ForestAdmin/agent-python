import asyncio
import sys
from typing import cast
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.override.collection import OverrideCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType


class BaseTestOverrideCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class # type:ignore

        cls.collection_transaction = Collection("Transaction", cls.datasource)  # type:ignore
        cls.collection_transaction.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN
                ),  # type:ignore
                "description": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),  # type:ignore
                "amount_in_eur": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),  # type:ignore
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
        )

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, OverrideCollectionDecorator)
        self.decorated_collection_transaction = cast(
            OverrideCollectionDecorator, self.datasource_decorator.get_collection("Transaction")
        )


class TestOverrideCollectionDecorator(BaseTestOverrideCollectionDecorator):
    def test_schema_should_not_change(self):
        self.assertEqual(self.collection_transaction.schema, self.decorated_collection_transaction.schema)


class TestCreateOverrideCollectionDecorator(BaseTestOverrideCollectionDecorator):
    def test_should_call_original_create_when_no_handler(self):
        with patch.object(
            self.collection_transaction, "create", wraps=self.collection_transaction.create
        ) as spy_create:
            self.loop.run_until_complete(
                self.decorated_collection_transaction.create(
                    self.mocked_caller, [{"description": "a transaction", "amount_in_eur": 38.4}]
                )
            )
            spy_create.assert_awaited_once_with(
                self.mocked_caller, [{"description": "a transaction", "amount_in_eur": 38.4}]
            )

    def test_should_call_custom_handler_when_set(self):
        handler = Mock()
        self.decorated_collection_transaction.add_create_handler(handler)
        with patch.object(
            self.collection_transaction, "create", wraps=self.collection_transaction.create
        ) as spy_create:

            self.loop.run_until_complete(
                self.decorated_collection_transaction.create(
                    self.mocked_caller, [{"description": "a transaction", "amount_in_eur": 38.4}]
                )
            )
            spy_create.assert_not_awaited()
            spy_create.assert_not_called()
            handler.assert_called_once()
            ctx = handler.call_args[0][0]
            self.assertEqual(ctx.data, [{"description": "a transaction", "amount_in_eur": 38.4}])
            self.assertEqual(ctx.caller, self.mocked_caller)

    def test_handler_should_be_awaited_when_its_async_method(self):
        handler = AsyncMock()
        self.decorated_collection_transaction.add_create_handler(handler)
        with patch.object(
            self.collection_transaction, "create", wraps=self.collection_transaction.create
        ) as spy_create:

            self.loop.run_until_complete(
                self.decorated_collection_transaction.create(
                    self.mocked_caller, [{"description": "a transaction", "amount_in_eur": 38.4}]
                )
            )
            spy_create.assert_not_awaited()
            spy_create.assert_not_called()
            handler.assert_awaited_once()
            ctx = handler.await_args[0][0]  # type:ignore
            self.assertEqual(ctx.data, [{"description": "a transaction", "amount_in_eur": 38.4}])
            self.assertEqual(ctx.caller, self.mocked_caller)


class TestUpdateOverrideCollectionDecorator(BaseTestOverrideCollectionDecorator):
    def test_should_call_original_update_when_no_handler(self):
        with patch.object(
            self.collection_transaction, "update", wraps=self.collection_transaction.update
        ) as spy_update:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})
            self.loop.run_until_complete(
                self.decorated_collection_transaction.update(
                    self.mocked_caller, filter_, {"description": "a transaction", "amount_in_eur": 38.4}
                )
            )
            spy_update.assert_awaited_once_with(
                self.mocked_caller, filter_, {"description": "a transaction", "amount_in_eur": 38.4}
            )

    def test_should_call_custom_handler_when_set(self):
        handler = Mock()
        self.decorated_collection_transaction.add_update_handler(handler)
        with patch.object(
            self.collection_transaction, "update", wraps=self.collection_transaction.update
        ) as spy_update:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})
            self.loop.run_until_complete(
                self.decorated_collection_transaction.update(
                    self.mocked_caller, filter_, {"description": "a transaction", "amount_in_eur": 38.4}
                )
            )
            spy_update.assert_not_awaited()
            spy_update.assert_not_called()
            handler.assert_called_once()
            ctx = handler.call_args[0][0]
            self.assertEqual(ctx.patch, {"description": "a transaction", "amount_in_eur": 38.4})
            self.assertEqual(ctx.caller, self.mocked_caller)
            self.assertEqual(ctx.filter, filter_)

    def test_handler_should_be_awaited_when_its_async_method(self):
        handler = AsyncMock()
        self.decorated_collection_transaction.add_update_handler(handler)
        with patch.object(
            self.collection_transaction, "update", wraps=self.collection_transaction.update
        ) as spy_update:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})

            self.loop.run_until_complete(
                self.decorated_collection_transaction.update(
                    self.mocked_caller, filter_, {"description": "a transaction", "amount_in_eur": 38.4}
                )
            )
            spy_update.assert_not_awaited()
            spy_update.assert_not_called()
            handler.assert_awaited_once()
            ctx = handler.await_args[0][0]  # type:ignore
            self.assertEqual(ctx.patch, {"description": "a transaction", "amount_in_eur": 38.4})
            self.assertEqual(ctx.caller, self.mocked_caller)
            self.assertEqual(ctx.filter, filter_)


class TestDeleteOverrideCollectionDecorator(BaseTestOverrideCollectionDecorator):
    def test_should_call_original_delete_when_no_handler(self):
        with patch.object(
            self.collection_transaction, "delete", wraps=self.collection_transaction.delete
        ) as spy_delete:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})
            self.loop.run_until_complete(self.decorated_collection_transaction.delete(self.mocked_caller, filter_))
            spy_delete.assert_awaited_once_with(self.mocked_caller, filter_)

    def test_should_call_custom_handler_when_set(self):
        handler = Mock()
        self.decorated_collection_transaction.add_delete_handler(handler)
        with patch.object(
            self.collection_transaction, "delete", wraps=self.collection_transaction.delete
        ) as spy_delete:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})
            self.loop.run_until_complete(self.decorated_collection_transaction.delete(self.mocked_caller, filter_))
            spy_delete.assert_not_awaited()
            spy_delete.assert_not_called()
            handler.assert_called_once()
            ctx = handler.call_args[0][0]
            self.assertEqual(ctx.caller, self.mocked_caller)
            self.assertEqual(ctx.filter, filter_)

    def test_handler_should_be_awaited_when_its_async_method(self):
        handler = AsyncMock()
        self.decorated_collection_transaction.add_delete_handler(handler)
        with patch.object(
            self.collection_transaction, "delete", wraps=self.collection_transaction.delete
        ) as spy_delete:
            filter_ = Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 1)})

            self.loop.run_until_complete(self.decorated_collection_transaction.delete(self.mocked_caller, filter_))
            spy_delete.assert_not_awaited()
            spy_delete.assert_not_called()
            handler.assert_awaited_once()
            ctx = handler.await_args[0][0]  # type:ignore
            self.assertEqual(ctx.caller, self.mocked_caller)
            self.assertEqual(ctx.filter, filter_)
