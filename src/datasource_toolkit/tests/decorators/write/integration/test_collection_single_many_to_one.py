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
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestSingleManyToOne(TestCase):
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
                "author_id": Column(
                    column_type=PrimitiveType.UUID,
                    type=FieldType.COLUMN,
                ),
                "my_author": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Person",
                    foreign_key="author_id",
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
                "price_id": Column(
                    column_type=PrimitiveType.UUID,
                    type=FieldType.COLUMN,
                ),
                "my_price": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Price",
                    foreign_key="price_id",
                    foreign_key_target="id",
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_person)
        cls.collection_prices = Collection("Price", cls.datasource)
        cls.collection_prices.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    is_read_only=True,
                    filter_operators=[Operator.IN, Operator.EQUAL],
                ),
                "value": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.datasource.add_collection(cls.collection_prices)

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
        self.collection_price_decorated = self.datasource_decorator.get_collection("Price")

    def test_create_relations_and_attach_to_new_collection(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_author": {"name": "NAME TO CHANGE"},
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        book_list_patcher = patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "my_author": {"id": "123e4567-e89b-12d3-a456-111111111111"}},
                {"id": 2, "my_author": {"id": "123e4567-e89b-12d3-a456-222222222222"}},
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

        condition_tree = ConditionTreeLeaf("a_field", Operator.PRESENT)
        filter_ = PaginatedFilter({"condition_tree": condition_tree})

        self.loop.run_until_complete(
            self.collection_book_decorated.update(self.mocked_caller, filter_, {"title": "a title"})
        )
        # then
        book_update_mock.assert_not_awaited()
        book_list_mock.assert_awaited_with(self.mocked_caller, filter_, Projection("id", "my_author:id"))
        person_update_mock.assert_awaited_with(
            self.mocked_caller,
            Filter(
                {
                    "condition_tree": ConditionTreeLeaf(
                        "id",
                        Operator.IN,
                        ["123e4567-e89b-12d3-a456-111111111111", "123e4567-e89b-12d3-a456-222222222222"],
                    )
                }
            ),
            {"name": "NAME TO CHANGE"},
        )
        book_list_patcher.stop()
        book_update_patcher.stop()
        person_update_patcher.stop()

    def test_updates_a_second_degree_relation(self):
        # given
        mock_price_update = patch.object(self.collection_prices, "update", new_callable=AsyncMock).start()

        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_author": {"my_price": {"value": 10}},
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        book_list_patcher = patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"my_author": {"id": "123e4567-e89b-12d3-a456-111111111111"}},
            ],
        )
        book_list_mock = book_list_patcher.start()
        book_update_patcher = patch.object(
            self.collection_book,
            "update",
            new_callable=AsyncMock,
        )
        book_update_mock = book_update_patcher.start()

        person_list_patcher = patch.object(
            self.collection_person,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"my_price": {"id": "123e4567-e89b-12d3-a456-333333333333"}},
            ],
        )
        person_list_mock = person_list_patcher.start()

        # when
        condition_tree = ConditionTreeLeaf("a_field", Operator.PRESENT)
        filter_ = PaginatedFilter({"condition_tree": condition_tree})
        self.loop.run_until_complete(
            self.collection_book_decorated.update(self.mocked_caller, filter_, {"title": "a title"})
        )

        # then
        book_list_mock.assert_awaited_with(
            self.mocked_caller,
            filter_,
            Projection("id", "my_author:id"),
        )
        person_list_mock.assert_awaited_with(
            self.mocked_caller,
            PaginatedFilter(
                {"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, "123e4567-e89b-12d3-a456-111111111111")}
            ),
            Projection("id", "my_price:id"),
        )
        book_update_mock.assert_not_awaited()
        mock_price_update.assert_awaited_with(
            self.mocked_caller,
            Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, "123e4567-e89b-12d3-a456-333333333333")}),
            {"value": 10},
        )
        book_list_patcher.stop()
        book_update_patcher.stop()
        person_list_patcher.stop()

    def test_creates_the_relation_and_attaches_to_new_collection(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_author": {"name": "NAME TO CHANGE"},
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        patch_person_create = patch.object(
            self.collection_person,
            "create",
            new_callable=AsyncMock,
            return_value=[{"id": "123e4567-e89b-12d3-a456-111111111111", "name": "NAME TO CHANGE"}],
        )
        mock_person_create = patch_person_create.start()
        patch_book_create = patch.object(
            self.collection_book, "create", new_callable=AsyncMock, return_value=[{"title": "name"}]
        )
        mock_book_create = patch_book_create.start()

        # when
        self.loop.run_until_complete(self.collection_book_decorated.create(self.mocked_caller, [{"title": "a title"}]))

        # then
        mock_book_create.assert_awaited_once_with(
            self.mocked_caller,
            [
                {"author_id": "123e4567-e89b-12d3-a456-111111111111"},
            ],
        )
        mock_person_create.assert_awaited_once_with(self.mocked_caller, [{"name": "NAME TO CHANGE"}])

        patch_person_create.stop()
        patch_book_create.stop()

    def test_creates_the_relation_and_attaches_to_new_collection_2(self):
        # given
        title_definition = Mock(
            side_effect=lambda value, ctx: {
                "my_author": {"name": "NAME TO CHANGE"},
            }
        )
        self.collection_book_decorated.replace_field_writing("title", title_definition)

        patch_person_update = patch.object(
            self.collection_person,
            "update",
            new_callable=AsyncMock,
        )
        mock_person_update = patch_person_update.start()
        patch_book_create = patch.object(
            self.collection_book, "create", new_callable=AsyncMock, return_value=[{"title": "name"}]
        )
        mock_book_create = patch_book_create.start()

        # when
        self.loop.run_until_complete(
            self.collection_book_decorated.create(
                self.mocked_caller, [{"title": "a title", "author_id": "123e4567-e89b-12d3-a456-111111111111"}]
            )
        )

        # then
        mock_book_create.assert_awaited_once_with(
            self.mocked_caller,
            [
                {"author_id": "123e4567-e89b-12d3-a456-111111111111"},
            ],
        )
        mock_person_update.assert_awaited_once_with(
            self.mocked_caller,
            Filter({"condition_tree": ConditionTreeLeaf("id", Operator.EQUAL, "123e4567-e89b-12d3-a456-111111111111")}),
            {"name": "NAME TO CHANGE"},
        )
        patch_person_update.stop()
        patch_book_create.stop()
