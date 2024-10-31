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
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_replace_collection import (
    WriteReplaceCollection,
)
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType


class TestWriteRelation(TestCase):
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
                "author": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_key="author_id",
                    foreign_key_target="id",
                    foreign_collection="Person",
                ),
                "author_first_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "author_last_name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
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
                "first_name_alias": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
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
        self.datasource_decorator = DatasourceDecorator(self.datasource, WriteReplaceCollection)
        self.collection_book_decorated = self.datasource_decorator.get_collection("Book")
        self.collection_person_decorated = self.datasource_decorator.get_collection("Person")

    def test_should_create_related_record_when_relation_not_set(self):
        def first_name_handler(value, context: WriteCustomizationContext):
            return {"author": {"first_name": value}}

        first_name_handler_mock = Mock(side_effect=first_name_handler)

        def last_name_handler(value, context: WriteCustomizationContext):
            return {"author": {"last_name": value}}

        last_name_handler_mock = Mock(side_effect=last_name_handler)

        self.collection_book_decorated.replace_field_writing("author_first_name", first_name_handler_mock)
        self.collection_book_decorated.replace_field_writing("author_last_name", last_name_handler_mock)

        with patch.object(self.collection_book, "create", new_callable=AsyncMock, return_value=[]) as mock_book_create:
            self.loop.run_until_complete(
                self.collection_book_decorated.create(
                    self.mocked_caller,
                    [
                        {"title": "Memories", "author_first_name": "John", "author_last_name": "Doe"},
                        {"title": "Future", "author_first_name": "Jane", "author_last_name": "Doe"},
                    ],
                )
            )
            mock_book_create.assert_any_await(
                self.mocked_caller,
                [
                    {"title": "Memories", "author": {"first_name": "John", "last_name": "Doe"}},
                    {"title": "Future", "author": {"first_name": "Jane", "last_name": "Doe"}},
                ],
            )
        first_name_handler_mock.assert_any_call("John", ANY)
        last_name_handler_mock.assert_any_call("Doe", ANY)
        first_name_handler_mock.assert_any_call("Jane", ANY)
        last_name_handler_mock.assert_any_call("Doe", ANY)

    def test_should_call_handler_of_related_relation(self):
        async def first_name_handler(value, context: WriteCustomizationContext):
            return {"first_name": value}

        first_name_handler_mock = AsyncMock(wraps=first_name_handler)

        self.collection_person_decorated.replace_field_writing("first_name_alias", first_name_handler_mock)
        self.collection_book_decorated.replace_field_writing(
            "author_first_name", lambda value, ctx: {"author": {"first_name_alias": value}}
        )
        self.collection_book_decorated.replace_field_writing(
            "author_last_name", lambda value, ctx: {"author": {"last_name": value}}
        )

        with patch.object(self.collection_book, "create", new_callable=AsyncMock, return_value=[]) as mock_book_create:
            self.loop.run_until_complete(
                self.collection_book_decorated.create(
                    self.mocked_caller,
                    [
                        {"title": "Memories", "author_first_name": "John", "author_last_name": "Doe"},
                    ],
                )
            )
            mock_book_create.assert_any_await(
                self.mocked_caller,
                [
                    {"title": "Memories", "author": {"first_name": "John", "last_name": "Doe"}},
                ],
            )
        first_name_handler_mock.assert_any_call("John", ANY)
