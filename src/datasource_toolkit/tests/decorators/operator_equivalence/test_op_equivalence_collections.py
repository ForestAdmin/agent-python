import asyncio
import sys
from unittest import TestCase
from unittest.mock import patch

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from mock import AsyncMock

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.operators_equivalence.collections import (
    OperatorEquivalenceCollectionDecorator,
)
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldAlias,
    FieldType,
    ManyToOne,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter, PaginatedFilterComponent


class TestComputedCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN, Operator.PRESENT],
                    type=FieldType.COLUMN,
                ),
                "publication_date": Column(
                    column_type=PrimitiveType.DATE,
                    filter_operators=[Operator.LESS_THAN, Operator.EQUAL, Operator.GREATER_THAN],
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
                "birth_date": Column(
                    column_type=PrimitiveType.DATE,
                    type=FieldType.COLUMN,
                    filter_operators=[Operator.LESS_THAN, Operator.EQUAL, Operator.GREATER_THAN],
                ),
                # "book": OneToOne(origin_key="author_id", origin_key_target="id", foreign_collection="Book"),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
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
        self.datasource_decorator = DatasourceDecorator(self.datasource, OperatorEquivalenceCollectionDecorator)
        self.decorated_collection_book = self.datasource_decorator.get_collection("Book")

    def test_date_lower_greater_equal(self):
        pub_date_schema: FieldAlias = self.decorated_collection_book.schema["fields"]["publication_date"]

        assert len(pub_date_schema["filter_operators"]) > 20

    def test_relation_not_dropped(self):
        fields_schema = self.decorated_collection_book.schema["fields"]

        assert "publication_date" in fields_schema
        assert "author" in fields_schema

    def test_list_with_null_condition_tree(self):
        condition_tree = PaginatedFilter({})

        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mocked_collection_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, condition_tree, Projection("publication_date"))
            )
            mocked_collection_list.assert_awaited_with(
                self.mocked_caller, condition_tree, Projection("publication_date")
            )

    def test_list_not_modify_supported_operator(self):
        condition_tree = PaginatedFilter(
            PaginatedFilterComponent(condition_tree=ConditionTreeLeaf("publication_date", Operator.EQUAL, "some_date"))
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mocked_collection_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, condition_tree, Projection("publication_date"))
            )
            mocked_collection_list.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter(
                    PaginatedFilterComponent(
                        condition_tree=ConditionTreeLeaf("publication_date", Operator.EQUAL, "some_date")
                    )
                ),
                Projection("publication_date"),
            )

    def test_list_should_transform_in_to_equal(self):
        condition_tree = PaginatedFilter(
            PaginatedFilterComponent(condition_tree=ConditionTreeLeaf("publication_date", Operator.BLANK))
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mocked_collection_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, condition_tree, Projection("publication_date"))
            )
            mocked_collection_list.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter(
                    PaginatedFilterComponent(condition_tree=ConditionTreeLeaf("publication_date", Operator.EQUAL, None))
                ),
                Projection("publication_date"),
            )

    def test_list_should_transform_in_to_equal_over_relation(self):
        condition_tree = PaginatedFilter(
            PaginatedFilterComponent(condition_tree=ConditionTreeLeaf("author:birth_date", Operator.BLANK))
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mocked_collection_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, condition_tree, Projection("author:birth_date"))
            )
            mocked_collection_list.assert_awaited_with(
                self.mocked_caller,
                PaginatedFilter(
                    PaginatedFilterComponent(
                        condition_tree=ConditionTreeLeaf("author:birth_date", Operator.EQUAL, None)
                    )
                ),
                Projection("author:birth_date"),
            )
