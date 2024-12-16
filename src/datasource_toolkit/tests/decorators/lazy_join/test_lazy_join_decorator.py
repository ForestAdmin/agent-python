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
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.lazy_join.collection import LazyJoinCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, OneToMany, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestEmptyCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.datasource: Datasource = Datasource()
        cls.datasource.get_collection = lambda x: cls.datasource._collections[x]
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

        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "author_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    type=FieldType.COLUMN,
                ),
            }
        )
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "first_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "books": OneToMany(origin_key="author_id", origin_key_target="id", foreign_collection="Book"),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, LazyJoinCollectionDecorator)
        cls.decorated_book_collection = cls.datasource_decorator.get_collection("Book")

    def test_should_not_join_when_projection_ask_for_target_field_only(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "author_id": 2}, {"id": 2, "author_id": 5}],
        ) as mock_list:
            result = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter({}),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(self.mocked_caller, PaginatedFilter({}), Projection("id", "author_id"))

        # should contain author object, without author_id FK
        self.assertEqual([{"id": 1, "author": {"id": 2}}, {"id": 2, "author": {"id": 5}}], result)

    def test_should_join_when_projection_ask_for_multiple_fields_in_foreign_collection(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "author": {"id": 2, "first_name": "Isaac"}},
                {"id": 2, "author": {"id": 5, "first_name": "J.K."}},
            ],
        ) as mock_list:
            result = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter({}),
                    Projection("id", "author:id", "author:first_name"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller, PaginatedFilter({}), Projection("id", "author:id", "author:first_name")
            )

        self.assertEqual(
            [
                {"id": 1, "author": {"id": 2, "first_name": "Isaac"}},
                {"id": 2, "author": {"id": 5, "first_name": "J.K."}},
            ],
            result,
        )

    def test_should_not_join_when_condition_tree_is_on_foreign_key_target(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "author_id": 2}, {"id": 2, "author_id": 5}, {"id": 3, "author_id": 5}],
        ) as mock_list:
            self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:id", "in", [2, 5])}),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("author_id", "in", [2, 5])}),
                Projection("id", "author_id"),
            )

    def test_should_join_when_condition_tree_is_on_foreign_collection_fields(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "author_id": 2}, {"id": 2, "author_id": 5}, {"id": 3, "author_id": 5}],
        ) as mock_list:
            self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter(
                        {"condition_tree": ConditionTreeLeaf("author:first_name", "in", ["Isaac", "J.K."])}
                    ),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:first_name", "in", ["Isaac", "J.K."])}),
                Projection("id", "author_id"),
            )

    def test_should_disable_join_on_condition_tree_but_not_in_projection(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "author": {"first_name": "Isaac"}},
                {"id": 2, "author": {"first_name": "J.K."}},
                {"id": 3, "author": {"first_name": "J.K."}},
            ],
        ) as mock_list:
            response = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:id", "in", [2, 5])}),
                    Projection("id", "author:first_name"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("author_id", "in", [2, 5])}),
                Projection("id", "author:first_name"),
            )
        self.assertEqual(
            [
                {"id": 1, "author": {"first_name": "Isaac"}},
                {"id": 2, "author": {"first_name": "J.K."}},
                {"id": 3, "author": {"first_name": "J.K."}},
            ],
            response,
        )

    def test_should_disable_join_on_projection_but_not_in_condition_tree(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "author_id": 2},
                {"id": 2, "author_id": 5},
                {"id": 3, "author_id": 5},
            ],
        ) as mock_list:
            response = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter(
                        {"condition_tree": ConditionTreeLeaf("author:first_name", "in", ["Isaac", "J.K."])}
                    ),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller,
                PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:first_name", "in", ["Isaac", "J.K."])}),
                Projection("id", "author_id"),
            )
        self.assertEqual(
            [
                {"id": 1, "author": {"id": 2}},
                {"id": 2, "author": {"id": 5}},
                {"id": 3, "author": {"id": 5}},
            ],
            response,
        )

    def test_should_correctly_handle_null_relations(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[
                {"id": 1, "author_id": 2},
                {"id": 2, "author_id": None},
            ],
        ) as mock_list:
            result = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    PaginatedFilter({}),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(self.mocked_caller, PaginatedFilter({}), Projection("id", "author_id"))

        self.assertEqual(
            [
                {"id": 1, "author": {"id": 2}},
                {"id": 2, "author": None},
            ],
            result,
        )
