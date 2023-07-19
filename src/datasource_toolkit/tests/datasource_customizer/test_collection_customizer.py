import asyncio
import sys
from typing import Union
from unittest import TestCase
from unittest.mock import patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionSingle, Context
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder as ResultBuilderChart
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    Operator,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


class TestCollectionCustomizer(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=[Operator.LONGER_THAN],
                    type=FieldType.COLUMN,
                ),
                "reference": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "child_id": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                    filter_operators=[Operator.EQUAL, Operator.IN],
                ),
                "author_id": Column(
                    column_type=PrimitiveType.STRING, type=FieldType.COLUMN, is_read_only=True, is_sortable=True
                ),
                "author": ManyToOne(
                    foreign_collection="Person",
                    foreign_key="author_id",
                    foreign_key_target="id",
                    type=FieldType.MANY_TO_ONE,
                ),
                "persons": ManyToMany(
                    type=FieldType.MANY_TO_MANY,
                    origin_key="book_id",
                    origin_key_target="id",
                    foreign_key="person_id",
                    foreign_key_target="id",
                    foreign_collection="Person",
                    through_collection="BookPerson",
                ),
            }
        )
        cls.collection_book_person = Collection("BookPerson", cls.datasource)
        cls.collection_book_person.add_fields(
            {
                "person_id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book_id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "category": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Category",
                    foreign_key="category_id",
                    foreign_key_target="id",
                ),
                "person": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Person",
                    foreign_key="person_id",
                    foreign_key_target="id",
                ),
            }
        )

        cls.collection_person = Collection("Person", cls.datasource)
        cls.collection_person.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "name_read_only": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN, is_read_only=True),
                "books": ManyToMany(
                    origin_key="person_id",
                    origin_key_target="id",
                    foreign_key="book_id",
                    foreign_key_target="id",
                    foreign_collection="Book",
                    through_collection="BookPerson",
                    type=FieldType.MANY_TO_MANY,
                ),
            }
        )

        cls.collection_category = Collection("Category", cls.datasource)
        cls.collection_category.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "book_id": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "book": OneToMany(
                    type=FieldType.ONE_TO_MANY,
                    foreign_collection="Book",
                    origin_key="category_id",
                    origin_key_target="id",
                ),
                "person": ManyToOne(
                    type=FieldType.MANY_TO_ONE,
                    foreign_collection="Person",
                    foreign_key="person_id",
                    foreign_key_target="id",
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_book)
        cls.datasource.add_collection(cls.collection_book_person)
        cls.datasource.add_collection(cls.collection_person)
        cls.datasource.add_collection(cls.collection_category)

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
        self.datasource_customizer = DatasourceCustomizer()
        self.datasource_customizer.add_datasource(self.datasource, {})

        self.book_customizer = CollectionCustomizer(
            self.datasource_customizer, self.datasource_customizer.stack, "Book"
        )
        self.book_person_customizer = CollectionCustomizer(
            self.datasource_customizer, self.datasource_customizer.stack, "BookPerson"
        )
        self.person_customizer = CollectionCustomizer(
            self.datasource_customizer, self.datasource_customizer.stack, "Person"
        )
        self.category_customizer = CollectionCustomizer(
            self.datasource_customizer, self.datasource_customizer.stack, "Category"
        )

    def test_add_field_should_add_a_field_to_early_collection(self):
        data = [{"id": 1, "title": "Foundation"}, {"id": 2, "title": "Harry Potter"}]

        async def get_values(records, context):
            return [f'{record["title"]}-2022' for record in records]

        computed_definition = ComputedDefinition(
            column_type=PrimitiveType.STRING, dependencies=["title"], get_values=get_values
        )
        self.book_customizer.add_field("test", computed_definition)
        computed_collection = self.datasource_customizer.stack.early_computed.get_collection("Book")

        returned_data = self.loop.run_until_complete(computed_collection.get_computed("test")["get_values"](data, None))

        assert "test" in computed_collection._computeds
        assert returned_data == ["Foundation-2022", "Harry Potter-2022"]

    # def test_add_field_should_add_a_field_to_late_collection(self):

    def test_add_segment_should_add_a_segment(self):
        self.book_customizer.add_segment("new_segment", lambda ctx: ConditionTreeLeaf("id", Operator.GREATER_THAN, 1))
        stack = self.datasource_customizer.stack
        assert "new_segment" in stack.segment.get_collection("Book")._segments

    def test_replace_search_should_call_search_decorator(self):
        def search_replacer(search, extended_search, context):
            return ConditionTreeLeaf("title", Operator.EQUAL, search)

        self.book_customizer.replace_search(search_replacer)

        assert self.datasource_customizer.stack.search.get_collection("Book")._replacer == search_replacer

    def test_disable_count_should_disable_count_on_collection(self):
        self.book_customizer.disable_count()

        assert self.datasource_customizer.stack.schema.get_collection("Book").schema["countable"] is False

    def test_rename_field_should_rename_field_in_collection(self):
        self.book_customizer.rename_field("title", "new_title")

        schema = self.datasource_customizer.stack.rename_field.get_collection("Book").schema
        assert "new_title" in schema["fields"]
        assert "title" not in schema["fields"]

    def test_remove_field_should_remove_field_in_collection(self):
        self.book_customizer.remove_field("title")
        schema = self.datasource_customizer.stack.publication.get_collection("Book").schema
        assert "title" not in schema["fields"]

    def test_add_action_should_add_action_in_collection(self):
        class ActionMan(ActionSingle):
            async def execute(self, context: Context, result_builder: ResultBuilder) -> Union[None, ActionResult]:
                return None

        self.book_customizer.add_action("action_man", ActionMan())

        schema = self.datasource_customizer.stack.publication.get_collection("Book").schema
        assert "action_man" in schema["actions"]

    def test_add_validation(self):
        self.person_customizer.add_validation("name", {"operator": Operator.LONGER_THAN, "value": 5})

        schema = self.datasource_customizer.stack.publication.get_collection("Person").schema
        assert schema["fields"]["name"]["validations"] == [{"operator": Operator.LONGER_THAN, "value": 5}]

    def test_add_chart(self):
        def chart_fn(context: CollectionChartContext, result_builder: ResultBuilderChart):
            return result_builder.value(1)

        with patch.object(
            self.datasource_customizer.stack.chart.get_collection("Book"), "add_chart"
        ) as mocked_add_chart:
            self.book_customizer.add_chart("test_chart", chart_fn)
            mocked_add_chart.assert_called_once_with("test_chart", chart_fn)

        self.book_customizer.add_chart("test_chart", chart_fn)
        schema = self.datasource_customizer.stack.publication.get_collection("Book").schema
        assert "test_chart" in schema["charts"]
        assert schema["charts"]["test_chart"] == chart_fn

    def test_replace_field_writing(self):
        def write_definition(value, context):
            return {"name": value}

        with patch.object(
            self.datasource_customizer.stack.write.get_collection("Person"), "replace_field_writing"
        ) as mocked_replace_field_writing:
            self.person_customizer.replace_field_writing("name", write_definition)
            mocked_replace_field_writing.assert_called_once_with("name", write_definition)
