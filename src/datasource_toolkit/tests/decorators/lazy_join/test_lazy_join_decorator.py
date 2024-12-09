import asyncio
import sys
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from forestadmin.datasource_toolkit.decorators.lazy_join.collection import LazyJoinCollectionDecorator

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, OneToOne, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
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
                "book": OneToOne(origin_key="author_id", origin_key_target="id", foreign_collection="Book"),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, LazyJoinCollectionDecorator)
        cls.decorated_book_collection = cls.datasource_decorator.get_collection("Book")

    def test_should_not_join_when_projection_ask_for_target_field_only(self):
        with patch.object(
            self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id": 1, "author_id": 1}]
        ) as mock_list:
            result = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    Filter({}),
                    Projection("id", "author:id"),
                )
            )
            mock_list.assert_awaited_once_with(self.mocked_caller, Filter({}), Projection("id", "author_id"))

        # should contain author object, without author_id FK
        self.assertEqual([{"id": 1, "author": {"id": 1}}], result)

    def test_should_join_when_projection_ask_for_multiple_fields_in_relation(self):
        with patch.object(
            self.collection_book,
            "list",
            new_callable=AsyncMock,
            return_value=[{"id": 1, "author": {"id": 1, "first_name": "Isaac"}}],
        ) as mock_list:
            result = self.loop.run_until_complete(
                self.decorated_book_collection.list(
                    self.mocked_caller,
                    Filter({}),
                    Projection("id", "author:id", "author:first_name"),
                )
            )
            mock_list.assert_awaited_once_with(
                self.mocked_caller, Filter({}), Projection("id", "author:id", "author:first_name")
            )

        self.assertEqual([{"id": 1, "author": {"id": 1, "first_name": "Isaac"}}], result)
