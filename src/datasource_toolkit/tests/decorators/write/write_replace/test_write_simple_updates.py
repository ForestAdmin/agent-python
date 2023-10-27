import asyncio
import sys
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_replace_collection import (
    WriteReplaceCollection,
)
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class TestWriteSimpleUpdates(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "age": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "price": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
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
        cls.empty_filter = Filter({})

    def setUp(self) -> None:
        self.datasource_decorator = DatasourceDecorator(self.datasource, WriteReplaceCollection)
        self.collection_book_decorated = self.datasource_decorator.get_collection("Book")

    def test_should_do_nothing(self):
        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"name": "a name"})
            )

            mock_book_update.assert_any_await(self.mocked_caller, self.empty_filter, {"name": "a name"})

    def test_should_work_with_empty_handler(self):
        handler = Mock(side_effect=lambda val, ctx: None)
        self.collection_book_decorated.replace_field_writing("name", handler)

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(
                    self.mocked_caller, self.empty_filter, {"name": "a name", "age": "some age"}
                )
            )

            mock_book_update.assert_any_await(self.mocked_caller, self.empty_filter, {"age": "some age"})
        handler.assert_called_with("a name", ANY)

    def test_should_work_writing_on_the_same_field_in_handler(self):
        handler = Mock(side_effect=lambda val, ctx: {"name": "another name"})
        self.collection_book_decorated.replace_field_writing("name", handler)

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"name": "a name"})
            )

            mock_book_update.assert_any_await(self.mocked_caller, self.empty_filter, {"name": "another name"})
        handler.assert_called_with("a name", ANY)

    def test_should_work_writing_another_field_in_handler(self):
        handler = Mock(side_effect=lambda val, ctx: {"age": "some age"})
        self.collection_book_decorated.replace_field_writing("name", handler)

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"name": "a name"})
            )

            mock_book_update.assert_any_await(self.mocked_caller, self.empty_filter, {"age": "some age"})
        handler.assert_called_with("a name", ANY)

    def test_should_work_when_unrelated_rewritters_are_used_in_parallel(self):
        age_handler = Mock(side_effect=lambda val, ctx: {"age": "new age"})
        self.collection_book_decorated.replace_field_writing("age", age_handler)

        price_handler = Mock(side_effect=lambda val, ctx: {"price": "new price"})
        self.collection_book_decorated.replace_field_writing("price", price_handler)

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(
                    self.mocked_caller, self.empty_filter, {"name": "name", "price": "price", "age": "age"}
                )
            )

            mock_book_update.assert_any_await(
                self.mocked_caller, self.empty_filter, {"name": "name", "price": "new price", "age": "new age"}
            )
        age_handler.assert_called_with("age", ANY)
        price_handler.assert_called_with("price", ANY)

    def test_should_work_doing_nested_rewritting(self):
        age_handler = Mock(side_effect=lambda val, ctx: {"price": "some price"})
        self.collection_book_decorated.replace_field_writing("age", age_handler)

        name_handler = Mock(side_effect=lambda val, ctx: {"age": "some age"})
        self.collection_book_decorated.replace_field_writing("name", name_handler)

        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mock_book_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"name": "a name"})
            )

            mock_book_update.assert_any_await(self.mocked_caller, self.empty_filter, {"price": "some price"})
        age_handler.assert_called_with("some age", ANY)
        name_handler.assert_called_with("a name", ANY)

    def test_should_throw_when_two_handlers_request_conflicts_updates(self):
        self.collection_book_decorated.replace_field_writing("name", lambda value, ctx: {"price": "123"})
        self.collection_book_decorated.replace_field_writing("age", lambda value, ctx: {"price": "456"})

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Conflict value on the field price. It received several values.",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(
                self.mocked_caller, self.empty_filter, {"name": "a name", "age": "an age"}
            ),
        )

    def test_should_raise_when_handler_call_themselves_recursively(self):
        self.collection_book_decorated.replace_field_writing("name", lambda value, ctx: {"age": "some age"})
        self.collection_book_decorated.replace_field_writing("age", lambda value, ctx: {"price": "some price"})
        self.collection_book_decorated.replace_field_writing("price", lambda value, ctx: {"name": "some name"})

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cycle detected: name -> age -> price.",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"name": "a name"}),
        )

    def test_should_raise_when_handler_return_unexpected_type(self):
        self.collection_book_decorated.replace_field_writing("age", lambda value, ctx: "RETURN_SHOULD_FAIL")

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳The write handler of age should return an object or nothing.",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"age": "10"}),
        )

    def test_should_throw_when_handler_return_unknown_field(self):
        self.collection_book_decorated.replace_field_writing("age", lambda value, ctx: {"author": "Asimov"})

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Unknown field : author",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"age": "10"}),
        )

    def test_should_throw_when_handler_return_unknown_relation(self):
        self.collection_book_decorated.replace_field_writing(
            "age", lambda value, ctx: {"author": {"last_name": "Asimov"}}
        )

        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Unknown field : author",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"age": "10"}),
        )

    def test_should_throw_if_customer_attemps_to_update_patch_in_handler(self):
        def handler(value, context):
            context.record["ADDED_FIELD"] = "updating the patch"

        self.collection_book_decorated.replace_field_writing("age", handler)

        self.assertRaisesRegex(
            TypeError,
            r"'mappingproxy' object does not support item assignment",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"age": "10"}),
        )

    def test_should_throw_when_handler_throw(self):
        def handler(value, context):
            raise Exception("Test Exc")

        self.collection_book_decorated.replace_field_writing("age", handler)

        self.assertRaisesRegex(
            Exception,
            r"Test Exc",
            self.loop.run_until_complete,
            self.collection_book_decorated.update(self.mocked_caller, self.empty_filter, {"age": "10"}),
        )
