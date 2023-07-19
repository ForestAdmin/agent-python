import asyncio
import sys
from unittest import TestCase, skip
from unittest.mock import Mock, patch

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
from forestadmin.datasource_toolkit.decorators.write.write_datasource_decorator import WriteDataSourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, OneToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestCollectionSingleOneToOne(TestCase):
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
                "my_owner": OneToOne(
                    type=FieldType.ONE_TO_ONE, foreign_collection="Person", origin_key="book_id", origin_key_target="id"
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

    def test_updates_the_right_relation_collection_with_right_param(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_owner": {"name": "NAME TO CHANGE"},
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        book_list_patcher = patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {
                    "id": "123e4567-e89b-12d3-a456-111111111111",
                    "my_owner": {"id": "123e4567-e89b-12d3-a456-000000000000"},
                },
            ],
        )
        book_list_mock = book_list_patcher.start()
        book_update_patcher = patch.object(
            self.collection_book,
            "update",
            new_callable=AsyncMock,
        )
        book_update_mock = book_update_patcher.start()
        person_update_patcher = patch.object(
            self.collection_person,
            "update",
            new_callable=AsyncMock,
        )
        person_update_mock = person_update_patcher.start()

        # when
        filter_ = Filter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "a name")})
        self.loop.run_until_complete(
            self.collection_book_decorated.update(self.mocked_caller, filter_, {"title": "a title"})
        )

        # then
        book_list_mock.assert_awaited_once_with(self.mocked_caller, filter_, Projection("id", "my_owner:id"))
        book_update_mock.assert_not_awaited()
        person_update_mock.assert_awaited_with(
            self.mocked_caller,
            Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, "123e4567-e89b-12d3-a456-000000000000")}),
            {"name": "NAME TO CHANGE"},
        )

        book_list_patcher.stop()
        book_update_patcher.stop()
        person_update_patcher.stop()

    # Romain:
    # I'm skipping this test because I'm really not sure that this behavior is correct so I
    # removed it while refactoring the write decorator.
    #
    # It relies on specifying a field in the created record that is not in the schema, which
    # will break as soon as we have better validation.
    #
    # Note that I did keep the behavior for many to one relations, which feel more natural.
    # If this gets reintroduced, I think the syntax should be the same for both types of relations.
    #
    # decoratedBooks.replaceFieldWriting('title', { myOwner: { id: value, name: 'newName' } });

    @skip
    def test_updates_the_relation_and_attaches_to_the_new_collection(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {"my_owner": {"name": "NAME TO CHANGE"}, "title": "name"}
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        book_create_patcher = patch.object(
            self.collection_book, "create", new_callable=AsyncMock, return_value=[{"title": "name"}]
        )
        book_create_mock = book_create_patcher.start()
        person_update_patcher = patch.object(self.collection_book, "update", new_callable=AsyncMock)
        person_update_mock = person_update_patcher.start()

        self.loop.run_until_complete(
            self.collection_book_decorated.create(
                self.mocked_caller, [{"title": "a title", "book_id": "123e4567-e89b-12d3-a456-111111111111"}]
            )
        )

        # then
        book_create_mock.assert_awaited_with(self.mocked_caller, [{"title": "name"}])
        person_update_mock.assert_awaited_with(
            self.mocked_caller,
            Filter(
                {"condition_tree": ConditionTreeLeaf("book_id", Operator.EQUAL, "123e4567-e89b-12d3-a456-111111111111")}
            ),
            {"name": "NAME TO CHANGE"},
        )

        book_create_patcher.stop()
        person_update_patcher.stop()
