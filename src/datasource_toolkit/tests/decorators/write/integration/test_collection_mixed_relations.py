import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, Mock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.write.write_datasource_decorator import WriteDataSourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToOne,
    OneToOne,
    Operator,
    PrimitiveType,
)


class TestCollectionMixedRelation(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
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
                "my_author": OneToOne(
                    type=FieldType.ONE_TO_ONE, foreign_collection="Person", origin_key="book_id", origin_key_target="id"
                ),
                "format_id": Column(
                    column_type=PrimitiveType.UUID,
                    type=FieldType.COLUMN,
                ),
                "my_format": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Format",
                    foreign_key="format_id",
                    foreign_key_target="id",
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_book)
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                ),
                "name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
                "book_id": Column(
                    column_type=PrimitiveType.UUID,
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_person)
        cls.collection_format = Collection("Format", cls.datasource)
        cls.collection_format.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                ),
                "name": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_format)

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
        self.datasource_decorator = WriteDataSourceDecorator(self.datasource)
        self.collection_book_decorated = self.datasource_decorator.get_collection("Book")
        self.collection_person_decorated = self.datasource_decorator.get_collection("Person")
        self.collection_format_decorated = self.datasource_decorator.get_collection("Format")

    def test_create_relations_and_attach_to_new_collection(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_author": {"name": "Orius"},
                "my_format": {"name": "XXL"},
                "title": "a name",
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        book_create_patcher = patch.object(
            self.collection_book,
            "create",
            new_callable=AsyncMock,
            return_value=[{"id": "123e4567-e89b-12d3-a456-426614174087", "title": "a name"}],
        )
        book_create_mock = book_create_patcher.start()

        person_create_patcher = patch.object(
            self.collection_person,
            "create",
            new_callable=AsyncMock,
            return_value=[{"id": "123e4567-e89b-12d3-a456-111111111111", "title": "Orius"}],
        )
        person_create_mock = person_create_patcher.start()

        format_create_patcher = patch.object(
            self.collection_format,
            "create",
            new_callable=AsyncMock,
            return_value=[{"id": "123e4567-e89b-12d3-a456-222222222222", "title": "XXL"}],
        )
        format_create_mock = format_create_patcher.start()

        # when
        self.loop.run_until_complete(self.collection_book_decorated.create(self.mocked_caller, [{"title": "a title"}]))

        # then
        book_create_mock.assert_awaited_once_with(
            self.mocked_caller, [{"format_id": "123e4567-e89b-12d3-a456-222222222222", "title": "a name"}]
        )
        person_create_mock.assert_awaited_once_with(
            self.mocked_caller, [{"book_id": "123e4567-e89b-12d3-a456-426614174087", "name": "Orius"}]
        )
        format_create_mock.assert_awaited_once_with(self.mocked_caller, [{"name": "XXL"}])

        book_create_patcher.stop()
        person_create_patcher.stop()
        format_create_patcher.stop()
