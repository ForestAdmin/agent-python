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
from forestadmin.datasource_toolkit.decorators.operators_emulate.collections import OperatorsEmulateCollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.validations.condition_tree import ConditionTreeValidatorException


class TestEmulateOperatorCollectionDecorator(TestCase):
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
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                ),
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
                    filter_operators=set(),
                ),
            }
        )
        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                ),
                "first_name": Column(
                    column_type=PrimitiveType.STRING, type=FieldType.COLUMN, filter_operators=set([Operator.EQUAL])
                ),
                "last_name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
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
        self.datasource_decorator = DatasourceDecorator(self.datasource, OperatorsEmulateCollectionDecorator)
        self.decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.decorated_collection_person = self.datasource_decorator.get_collection("Person")

    def test_should_throw_when_pk_does_not_support_in_or_equal(self):
        datasource = Datasource()
        collection_book = Collection("Book", datasource)
        collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN, filter_operators=set()
                ),
            }
        )
        datasource.add_collection(collection_book)
        datasource_decorator = DatasourceDecorator(datasource, OperatorsEmulateCollectionDecorator)
        decorated_collection_book = datasource_decorator.get_collection("Book")
        self.assertRaisesRegex(
            ForestException,
            "🌳🌳🌳Cannot override operators on collection 'Book': the primary key columns must support"
            + " 'Equal' and 'In' operators",
            decorated_collection_book.emulate_field_operator,
            "title",
            Operator.GREATER_THAN,
        )

    def test_emulate_operator_should_throw_if_field_does_not_exists(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            "🌳🌳🌳Column not found: Book.__dont_exist",
            self.decorated_collection_book.emulate_field_operator,
            "__dont_exist",
            Operator.EQUAL,
        )

    def test_emulate_operator_should_throw_if_field_is_a_relation(self):
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Unexpected field type: Book.author \(found FieldType\.MANY_TO_ONE expected Column\)",
            self.decorated_collection_book.emulate_field_operator,
            "author",
            Operator.EQUAL,
        )

    def test_emulate_operator_should_throw_if_field_is_in_a_relation(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳Cannot replace operator for relation on field 'author:first_name'",
            self.decorated_collection_book.emulate_field_operator,
            "author:first_name",
            Operator.EQUAL,
        )

    def test_list_should_crash_if_wanted_operator_not_supported(self):
        async def title_starts_with_replacer(value, ctx):
            return ConditionTreeLeaf("title", Operator.LIKE, "a_title_value%")

        self.decorated_collection_book.replace_field_operator("title", Operator.STARTS_WITH, title_starts_with_replacer)
        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mock_book_list:
            self.assertRaisesRegex(
                ConditionTreeValidatorException,
                r"🌳🌳🌳The given operator Operator.LIKE is not supported by the column: "
                + r"\"The allowed types are \[<Operator.STARTS_WITH: 'starts_with'>]\"",
                self.loop.run_until_complete,
                self.decorated_collection_book.list(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("title", Operator.STARTS_WITH, "Found")}),
                    Projection("id", "title"),
                ),
            )

            mock_book_list.assert_not_awaited()

    def test_list_should_crash_when_creating_a_cycle_in_replacement(self):
        self.decorated_collection_book.replace_field_operator(
            "title",
            Operator.STARTS_WITH,
            lambda value, ctx: ConditionTreeLeaf("title", Operator.LIKE, f"{value}%"),
        )
        self.decorated_collection_book.replace_field_operator(
            "title",
            Operator.LIKE,
            lambda value, ctx: ConditionTreeLeaf("title", Operator.STARTS_WITH, f"{value}%"),
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock) as mock_book_list:
            self.assertRaisesRegex(
                ForestException,
                r"🌳🌳🌳Operator replacement cycle: Book.title\[Operator.STARTS_WITH\] -> "
                + r"Book.title\[Operator.LIKE\] -> Book.title\[Operator.STARTS_WITH]",
                self.loop.run_until_complete,
                self.decorated_collection_book.list(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("title", Operator.STARTS_WITH, "Found")}),
                    Projection("id", "title"),
                ),
            )
            mock_book_list.assert_not_awaited()

    def test_when_emulate_an_operator_schema_should_support_given_operator(self):
        self.decorated_collection_person.emulate_field_operator("first_name", Operator.STARTS_WITH)

        self.assertEqual(
            self.decorated_collection_person.schema["fields"]["first_name"]["filter_operators"],
            set([Operator.EQUAL, Operator.STARTS_WITH]),
        )

    def test_when_emulate_an_operator_list_should_not_rewrite_operator_from_another_operator(self):
        self.decorated_collection_person.emulate_field_operator("first_name", Operator.STARTS_WITH)

        with patch.object(
            self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id": 2, "title": "Foundation"}]
        ) as mock_book_list:
            with patch.object(
                self.collection_person, "list", new_callable=AsyncMock, return_value=[]
            ) as mock_person_list:
                records = self.loop.run_until_complete(
                    self.decorated_collection_book.list(
                        self.mocked_caller,
                        PaginatedFilter(
                            {"condition_tree": ConditionTreeLeaf("author:first_name", Operator.EQUAL, "Isaac")}
                        ),
                        Projection("id", "title"),
                    ),
                )
                self.assertEqual(records, [{"id": 2, "title": "Foundation"}])
                mock_book_list.assert_awaited_once_with(
                    self.mocked_caller,
                    PaginatedFilter(
                        {"condition_tree": ConditionTreeLeaf("author:first_name", Operator.EQUAL, "Isaac")}
                    ),
                    Projection("id", "title"),
                )
                mock_person_list.assert_not_awaited()

    def test_when_emulate_an_operator_list_should_find_book_form_related_collection(self):
        self.decorated_collection_person.emulate_field_operator("first_name", Operator.STARTS_WITH)

        with patch.object(
            self.collection_book, "list", new_callable=AsyncMock, return_value=[{"id": 2, "title": "Foundation"}]
        ) as mock_book_list:
            with patch.object(
                self.collection_person,
                "list",
                new_callable=AsyncMock,
                return_value=[
                    {"id": 1, "first_name": "Edward"},
                    {"id": 2, "first_name": "Isaac"},
                ],
            ) as mock_person_list:
                records = self.loop.run_until_complete(
                    self.decorated_collection_book.list(
                        self.mocked_caller,
                        PaginatedFilter(
                            {"condition_tree": ConditionTreeLeaf("author:first_name", Operator.STARTS_WITH, "Isaa")}
                        ),
                        Projection("id", "title"),
                    ),
                )

                self.assertEqual(records, [{"id": 2, "title": "Foundation"}])

                mock_person_list.assert_awaited_once_with(
                    self.mocked_caller, PaginatedFilter({}), Projection("first_name", "id")
                )

                mock_book_list.assert_awaited_once_with(
                    self.mocked_caller,
                    PaginatedFilter({"condition_tree": ConditionTreeLeaf("author:id", Operator.EQUAL, 2)}),
                    Projection("id", "title"),
                )

    def test_when_implement_an_operator_in_the_less_efficient_way_list_should_work(self):
        # Emulate title 'ShorterThan' and 'Contains'
        self.decorated_collection_book.emulate_field_operator("title", Operator.SHORTER_THAN)
        self.decorated_collection_book.emulate_field_operator("title", Operator.CONTAINS)

        # Define 'Equal(x)' to be 'Contains(x) && ShorterThan(x.length + 1)'
        self.decorated_collection_book.replace_field_operator(
            "title",
            Operator.EQUAL,
            lambda value, ctx: ConditionTreeBranch(
                Aggregator.AND,
                [
                    ConditionTreeLeaf("title", Operator.CONTAINS, value),
                    ConditionTreeLeaf("title", Operator.SHORTER_THAN, len(value) + 1),
                ],
            ),
        )

        async def mock_book_list_fn(caller: User, filter_: PaginatedFilter, projection: Projection):
            if filter_ and filter_.condition_tree:
                using_forbidden_operator = filter_.condition_tree.some_leaf(
                    lambda leaf: leaf.field != "id"
                    and leaf.operator not in self.collection_book.schema["fields"]["id"]["filter_operators"]
                )
                self.assertFalse(using_forbidden_operator)

            # perform request
            child_records = [
                {"id": 1, "title": "Beat the dealer"},
                {"id": 2, "title": "Foundation"},
                {"id": 3, "title": "Papillon"},
            ]

            if filter_ and filter_.condition_tree:
                child_records = filter_.condition_tree.filter(child_records, self.collection_book, caller.timezone)

            return projection.apply(child_records)

        filter_ = PaginatedFilter({"condition_tree": ConditionTreeLeaf("title", Operator.EQUAL, "Foundation")})
        with patch.object(self.collection_book, "list", side_effect=mock_book_list_fn):
            records = self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, filter_, Projection("id", "title"))
            )

        self.assertEqual(records, [{"id": 2, "title": "Foundation"}])
        # Not checking the calls to the underlying collection, as current implementation is quite
        # naive and could be greatly improved if there is a need.
