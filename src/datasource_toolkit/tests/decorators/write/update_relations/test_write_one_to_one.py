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
from forestadmin.datasource_toolkit.decorators.write.write_datasource_decorator import WriteDataSourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, OneToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestWriteOneToOne(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                ),
                "author_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    is_sortable=True,
                ),
                "author": OneToOne(
                    type=FieldType.ONE_TO_ONE,
                    origin_key="author_id",
                    origin_key_target="id",
                    foreign_collection="Person",
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_book)
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                ),
                "first_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "last_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "book_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_person)

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
        self.datasource_decorator = WriteDataSourceDecorator(self.datasource)
        self.collection_book_decorated = self.datasource_decorator.get_collection("Book")
        self.collection_person_decorated = self.datasource_decorator.get_collection("Person")

    def test_should_proxy_the_call_without_changes(self):
        filter_ = Filter({})
        with patch.object(self.collection_book, "update", new_callable=AsyncMock) as mocked_update:
            self.loop.run_until_complete(
                self.collection_book_decorated.update(self.mocked_caller, filter_, {"title": "New title"})
            )
            mocked_update.assert_awaited_once_with(self.mocked_caller, filter_, {"title": "New title"})

    def test_should_create_related_record_when_not_exists(self):
        condition_tree = {"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 3)}
        filter_ = Filter(condition_tree)

        patch_update_book = patch.object(
            self.collection_book,
            "update",
            new_callable=AsyncMock,
        )
        mock_update_book = patch_update_book.start()
        patch_list_book = patch.object(
            self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id": 3, "author": None}]
        )
        mock_list_book = patch_list_book.start()
        patch_create_person = patch.object(
            self.collection_person,
            "create",
            new_callable=AsyncMock,
            return_value=[{"id": 3, "first_name": "John", "last_name": "Doe"}],
        )
        mock_create_person = patch_create_person.start()

        self.loop.run_until_complete(
            self.collection_book_decorated.update(
                self.mocked_caller,
                filter_,
                {"title": "new title", "author": {"first_name": "John", "last_name": "Doe"}},
            )
        )

        mock_update_book.assert_any_await(self.mocked_caller, filter_, {"title": "new title"})
        mock_list_book.assert_any_await(
            self.mocked_caller, PaginatedFilter(condition_tree), Projection("id", "author:id")
        )

        mock_create_person.assert_any_await(self.mocked_caller, [{"first_name": "John", "last_name": "Doe"}])
        # why the next assertion is not made and asserted ?
        # mock_update_book.assert_any_await(self.mocked_caller, filter_, {"author_id": 3})

        patch_list_book.stop()
        patch_update_book.stop()
        patch_create_person.stop()

    def test_update_should_update_related_record_if_exists(self):
        condition_tree = {"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, 3)}
        filter_ = Filter(condition_tree)

        patch_update_book = patch.object(
            self.collection_book,
            "update",
            new_callable=AsyncMock,
        )
        mock_update_book = patch_update_book.start()
        patch_list_book = patch.object(
            self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id": 3, "author": {"id": 3}}]
        )
        mock_list_book = patch_list_book.start()
        patch_update_person = patch.object(
            self.collection_person,
            "update",
            new_callable=AsyncMock,
        )
        mock_update_person = patch_update_person.start()

        self.loop.run_until_complete(
            self.collection_book_decorated.update(
                self.mocked_caller,
                filter_,
                {"title": "new title", "author": {"first_name": "John"}},
            )
        )

        mock_update_book.assert_any_await(self.mocked_caller, filter_, {"title": "new title"})
        mock_list_book.assert_any_await(
            self.mocked_caller, PaginatedFilter(condition_tree), Projection("id", "author:id")
        )

        mock_update_person.assert_any_await(self.mocked_caller, filter_, {"first_name": "John"})

        patch_list_book.stop()
        patch_update_book.stop()
        patch_update_person.stop()
