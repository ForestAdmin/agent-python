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
from forestadmin.datasource_toolkit.decorators.computed.collections import ComputedCollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.exceptions import ComputedDecoratorException
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, OneToOne, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, PlainAggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


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
                "author_id": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
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
                "sub_title": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
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
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, ComputedCollectionDecorator)

        async def get_values(records, context):
            return [f"{record['first_name']} {record['last_name']}" for record in records]

        cls.datasource_decorator.get_collection("Person").register_computed(
            "full_name",
            ComputedDefinition(
                column_type=PrimitiveType.STRING,
                dependencies=["first_name", "last_name"],
                get_values=get_values,
            ),
        )
        cls.book_records = [
            {
                "id": 1,
                "author_id": 1,
                "author": {"id": 1, "first_name": "Isaac", "last_name": "Asimov"},
                "title": "Foundation",
            },
            {
                "id": 2,
                "author_id": 2,
                "author": {"id": 2, "first_name": "Edward O.", "last_name": "Thorp"},
                "title": "Beat the dealer",
            },
        ]

    def test_create_without_dependencies(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.assertRaisesRegex(
            ComputedDecoratorException,
            r"🌳🌳🌳Computed field 'Book\.new_field' must have at least one dependency",
            decorated_collection_book.register_computed,
            "new_field",
            ComputedDefinition(column_type=PrimitiveType.STRING, dependencies=[], get_values=lambda x: x),
        )

    def test_create_with_missing_dependencies(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳Column not found: Book\.__nonExisting__\. Fields in Book are id, author_id, author, title, sub_title",
            decorated_collection_book.register_computed,
            "new_field",
            ComputedDefinition(
                column_type=PrimitiveType.STRING, dependencies=["__nonExisting__"], get_values=lambda x: x
            ),
        )

    def test_create_with_wrong_dependencies(self):
        decorated_collection_book = self.datasource_decorator.get_collection("Book")
        self.assertRaisesRegex(
            DatasourceToolkitException,
            r"🌳🌳🌳Unexpected field type: Book\.author \(found FieldType\.MANY_TO_ONE expected Column\)",
            decorated_collection_book.register_computed,
            "new_field",
            ComputedDefinition(column_type=PrimitiveType.STRING, dependencies=["author"], get_values=lambda x: x),
        )

    def test_schema_contains_computed_field(self):
        decorated_collection_person = self.datasource_decorator.get_collection("Person")
        fields_schema = decorated_collection_person.schema["fields"]

        assert "full_name" in fields_schema
        assert fields_schema["full_name"]["column_type"] == PrimitiveType.STRING
        assert fields_schema["full_name"]["is_read_only"] is True

    def test_list_return_computed_field(self):
        async def get_values(records, context):
            return [f"{record['first_name']} {record['last_name']} - {context.caller.user_id}" for record in records]

        self.datasource_decorator.get_collection("Person").register_computed(
            "full_name_with_context",
            ComputedDefinition(
                column_type=PrimitiveType.STRING, dependencies=["first_name", "last_name"], get_values=get_values
            ),
        )
        book_decorated = self.datasource_decorator.get_collection("Book")
        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.book_records):
            results = self.loop.run_until_complete(
                book_decorated.list(
                    self.mocked_caller, PaginatedFilter({}), Projection("title", "author:full_name_with_context")
                )
            )

        assert results[0]["title"] == self.book_records[0]["title"]
        assert results[0]["author"]["full_name_with_context"] == "Isaac Asimov - 1"
        assert results[1]["title"] == self.book_records[1]["title"]
        assert results[1]["author"]["full_name_with_context"] == "Edward O. Thorp - 1"

    def test_get_values_can_be_callable_or_awaitables(self):
        def get_values(records, context):
            return [f"{record['first_name']} {record['last_name']}" for record in records]

        self.datasource_decorator.get_collection("Person").register_computed(
            "full_name_sync",
            ComputedDefinition(
                column_type=PrimitiveType.STRING,
                dependencies=["first_name", "last_name"],
                get_values=get_values,
            ),
        )
        book_decorated = self.datasource_decorator.get_collection("Book")
        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.book_records):
            results = self.loop.run_until_complete(
                book_decorated.list(
                    self.mocked_caller, PaginatedFilter({}), Projection("title", "author:full_name_sync")
                )
            )
        assert results[0]["title"] == self.book_records[0]["title"]
        assert results[0]["author"]["full_name_sync"] == "Isaac Asimov"
        assert results[1]["title"] == self.book_records[1]["title"]
        assert results[1]["author"]["full_name_sync"] == "Edward O. Thorp"

    def test_get_values_can_also_be_lambda(self):
        self.datasource_decorator.get_collection("Person").register_computed(
            "full_name_sync",
            ComputedDefinition(
                column_type=PrimitiveType.STRING,
                dependencies=["first_name", "last_name"],
                get_values=lambda records, context: [
                    f"{record['first_name']} {record['last_name']}" for record in records
                ],
            ),
        )
        book_decorated = self.datasource_decorator.get_collection("Book")
        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.book_records):
            results = self.loop.run_until_complete(
                book_decorated.list(
                    self.mocked_caller, PaginatedFilter({}), Projection("title", "author:full_name_sync")
                )
            )
        assert results[0]["title"] == self.book_records[0]["title"]
        assert results[0]["author"]["full_name_sync"] == "Isaac Asimov"
        assert results[1]["title"] == self.book_records[1]["title"]
        assert results[1]["author"]["full_name_sync"] == "Edward O. Thorp"

    def test_aggregate_no_computed(self):
        aggregation = Aggregation(PlainAggregation(operation="Count"))
        book_collection = self.datasource_decorator.get_collection("Book")

        with patch.object(
            self.collection_book,
            "aggregate",
            new_callable=AsyncMock,
            return_value=aggregation.apply(self.book_records, self.mocked_caller.timezone),
        ):
            result = self.loop.run_until_complete(
                book_collection.aggregate(self.mocked_caller, Filter({}), aggregation)
            )

        assert "value" in result[0]
        assert "group" in result[0]
        assert result[0]["value"] == 2
        assert result[0]["group"] == {}

    def test_aggregate_computed(self):
        aggregation = Aggregation(PlainAggregation(operation="Min", field="author:full_name"))
        book_collection = self.datasource_decorator.get_collection("Book")

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=self.book_records):
            result = self.loop.run_until_complete(
                book_collection.aggregate(self.mocked_caller, Filter({}), aggregation)
            )

        assert "value" in result[0]
        assert "group" in result[0]
        assert result[0]["value"] == "Edward O. Thorp"
        assert result[0]["group"] == {}
