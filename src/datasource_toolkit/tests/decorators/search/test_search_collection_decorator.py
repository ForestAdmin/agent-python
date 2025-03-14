import asyncio
import sys
from typing import Any
from unittest import TestCase
from unittest.mock import ANY, AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.search.collections import SearchCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PolymorphicManyToOne,
    PrimitiveType,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class TestSearchCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        Collection.__abstractmethods__ = set()  # to instantiate abstract class

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
        self.datasource: Datasource = Datasource()
        self.collection_person = Collection("Person", self.datasource)
        self.collection_person.add_fields(
            {
                "id": {
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.NUMBER,
                    "filter_operators": set([Operator.EQUAL, Operator.IN]),
                }
            }
        )

        self.no_searchable_fields_collection = Collection("NotSearchable", self.datasource)
        self.no_searchable_fields_collection.add_fields(
            {
                "id": {
                    "is_primary_key": True,
                    "type": FieldType.COLUMN,
                    "column_type": PrimitiveType.NUMBER,
                    "filter_operators": set(),
                }
            }
        )
        self.datasource.add_collection(self.collection_person)
        self.datasource.add_collection(self.no_searchable_fields_collection)

        self.datasource_decorator = DatasourceDecorator(self.datasource, SearchCollectionDecorator)
        self.decorated_collection_person: SearchCollectionDecorator = self.datasource_decorator.get_collection(
            "Person"
        )  # type:ignore

        self.decorated_not_searchable_collection: SearchCollectionDecorator = self.datasource_decorator.get_collection(
            "NotSearchable"
        )  # type:ignore

    def test_replace_search_should_work(self):
        def replacer(search: Any, search_extended: bool, context: CollectionCustomizationContext):
            return ConditionTreeBranch(Aggregator.AND, [ConditionTreeLeaf("id", Operator.EQUAL, 1)])

        self.decorated_collection_person.replace_search(replacer)
        assert self.decorated_collection_person._replacer == replacer

    def test_schema_is_searchable_should_be_true_by_default_when_fields_can_be_searched(self):
        assert self.decorated_collection_person.schema["searchable"] is True

    def test_schema_is_searchable_should_be_false_when_no_fields_can_be_searched(self):
        assert self.decorated_not_searchable_collection.schema["searchable"] is False

    def test_schema_conflict_on_replace_and_disable_apply_the_latest_one(self):
        self.decorated_collection_person.mark_schema_as_dirty()
        assert self.decorated_collection_person.schema["searchable"] is True

        self.decorated_collection_person.disable_search()
        self.decorated_collection_person.mark_schema_as_dirty()
        assert self.decorated_collection_person.schema["searchable"] is False

        self.decorated_collection_person.replace_search(None)
        self.decorated_collection_person.mark_schema_as_dirty()
        assert self.decorated_collection_person.schema["searchable"] is True

    def test_schema_is_searchable_should_be_false_when_disabling_search(self):
        self.decorated_collection_person.disable_search()
        assert self.decorated_collection_person.schema["searchable"] is False

    def test_refine_filter_should_return_the_given_filter_for_empty_filter(self):
        filter_ = Filter({"search": None})

        assert (
            self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
            == filter_
        )

    def test_refine_filter_should_return_the_given_filter(self):
        filter_ = Filter({"search": "a text"})

        with patch.dict(self.collection_person.schema, {"searchable": True}):
            returned_filter = self.loop.run_until_complete(
                self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
            )
        assert returned_filter == filter_

    def test_search_empty_string_should_return_search_null(self):
        filter_ = Filter({"search": "         "})

        assert self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        ) == Filter({"search": None, "condition_tree": None, "segment": None})

    def test_intersect_search_and_condition(self):
        self.collection_person.add_field(
            "label",
            Column(column_type=PrimitiveType.STRING, filter_operators=[Operator.CONTAINS], type=FieldType.COLUMN),
        )

        filter_ = Filter(
            {
                "search": "a text",
                "condition_tree": ConditionTreeBranch(
                    Aggregator.AND, [ConditionTreeLeaf("label", Operator.EQUAL, "value")]
                ),
            }
        )
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.AND,
                    [
                        ConditionTreeLeaf("label", Operator.EQUAL, "value"),
                        ConditionTreeLeaf("label", Operator.CONTAINS, "a text"),
                    ],
                ),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_search_uuid(self):
        self.collection_person.add_field(
            "number",
            Column(column_type=PrimitiveType.UUID, filter_operators=[Operator.EQUAL], type=FieldType.COLUMN),
        )
        filter_ = Filter(
            {
                "search": "2d162303-78bf-599e-b197-93590ac3d315",
            }
        )

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeLeaf("number", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_search_must_be_applied_on_all_fields(self):
        self.collection_person.add_field(
            "number",
            Column(column_type=PrimitiveType.NUMBER, filter_operators=[Operator.EQUAL], type=FieldType.COLUMN),
        )
        self.collection_person.add_field(
            "label",
            Column(column_type=PrimitiveType.STRING, filter_operators=[Operator.CONTAINS], type=FieldType.COLUMN),
        )
        filter_ = Filter(
            {
                "search": "1584",
            }
        )

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.OR,
                    conditions=[
                        ConditionTreeLeaf("id", Operator.EQUAL, 1584),
                        ConditionTreeLeaf("number", Operator.EQUAL, 1584),
                        ConditionTreeLeaf("label", Operator.CONTAINS, "1584"),
                    ],
                )
            }
        )

    def test_for_enum_value(self):
        self.collection_person.add_field(
            "label",
            Column(
                column_type=PrimitiveType.ENUM,
                filter_operators=[Operator.EQUAL],
                type=FieldType.COLUMN,
                enum_values=["AnEnUmVaLue"],
            ),
        )
        filter_ = Filter(
            {
                "search": "anenumvalue",
            }
        )
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeLeaf("label", Operator.EQUAL, "AnEnUmVaLue"),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_search_number_in_all_field(self):
        self.collection_person.add_field(
            "field1",
            Column(column_type=PrimitiveType.NUMBER, filter_operators=set([Operator.EQUAL]), type=FieldType.COLUMN),
        )
        self.collection_person.add_field(
            "field2",
            Column(column_type=PrimitiveType.NUMBER, filter_operators=set([Operator.EQUAL]), type=FieldType.COLUMN),
        )

        self.collection_person.add_field(
            "field_not_returned",
            Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
        )
        filter_ = Filter(
            {
                "search": "0001584",
            }
        )
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.OR,
                    conditions=[
                        ConditionTreeLeaf("id", Operator.EQUAL, 1584),
                        ConditionTreeLeaf("field1", Operator.EQUAL, 1584),
                        ConditionTreeLeaf("field2", Operator.EQUAL, 1584),
                    ],
                ),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_search_extended_over_relation(self):
        collection_book = Collection("Book", self.datasource)
        collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    filter_operators=[Operator.EQUAL],
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                ),
                "reviews": ManyToMany(
                    origin_key="book_id",
                    origin_key_target="id",
                    foreign_key="review_id",
                    foreign_key_target="id",
                    foreign_collection="Review",
                    through_collection="BookReview",
                    type=FieldType.MANY_TO_MANY,
                ),
                "book_reviews": OneToMany(
                    origin_key="book_id",
                    origin_key_target="id",
                    foreign_collection="Review",
                    type=FieldType.ONE_TO_MANY,
                ),
            }
        )
        collection_book_review = Collection("BookReview", self.datasource)
        collection_book_review.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    filter_operators=[Operator.EQUAL],
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                ),
                "reviews": ManyToMany(
                    origin_key="book_id",
                    origin_key_target="id",
                    foreign_key="review_id",
                    foreign_key_target="id",
                    foreign_collection="Review",
                    through_collection="BookReview",
                    type=FieldType.MANY_TO_MANY,
                ),
                "book": ManyToOne(
                    foreign_key="book_id",
                    foreign_key_target="id",
                    foreign_collection="Book",
                    type=FieldType.MANY_TO_ONE,
                ),
                "review": OneToOne(
                    origin_key="review_id",
                    origin_key_target="id",
                    foreign_collection="Review",
                    type=FieldType.ONE_TO_ONE,
                ),
            }
        )
        collection_review = Collection("Review", self.datasource)
        collection_review.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    filter_operators=[Operator.EQUAL],
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                ),
                "book": ManyToOne(
                    foreign_key="book_id",
                    foreign_key_target="id",
                    foreign_collection="Book",
                    type=FieldType.MANY_TO_ONE,
                ),
            }
        )
        self.datasource.add_collection(collection_book)
        self.datasource.add_collection(collection_book_review)
        self.datasource.add_collection(collection_review)
        self.datasource_decorator = DatasourceDecorator(self.datasource, SearchCollectionDecorator)

        filter_ = Filter({"search": "2d162303-78bf-599e-b197-93590ac3d315", "search_extended": True})

        decorated_collection_book_review = self.datasource_decorator.get_collection("BookReview")
        returned_filter = self.loop.run_until_complete(
            decorated_collection_book_review._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    aggregator=Aggregator.OR,
                    conditions=[
                        ConditionTreeLeaf("id", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                        ConditionTreeLeaf("book:id", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                        ConditionTreeLeaf("review:id", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                    ],
                ),
                "search": None,
                "search_extended": True,
                "segment": None,
            }
        )

    def test_search_extended_should_not_search_over_polymorphic_relations_and_show_a_debug_log(self):
        collection_book = Collection("Book", self.datasource)
        collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    filter_operators=[Operator.EQUAL],
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                ),
            }
        )
        collection_rating = Collection("Rating", self.datasource)
        collection_rating.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.UUID,
                    is_primary_key=True,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    type=FieldType.COLUMN,
                ),
                "rating": Column(column_type=PrimitiveType.NUMBER, type=FieldType.COLUMN),
                "target_id": Column(
                    column_type=PrimitiveType.UUID,
                    filter_operators=set([Operator.EQUAL, Operator.IN]),
                    type=FieldType.COLUMN,
                ),
                "target_type": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "target": PolymorphicManyToOne(
                    foreign_collections=["Book"],
                    foreign_key="target_id",
                    foreign_key_targets={"Book": "id"},
                    foreign_key_type_field="target_type",
                    type=FieldType.POLYMORPHIC_MANY_TO_ONE,
                ),
            }
        )
        self.datasource.add_collection(collection_rating)
        filter_ = Filter({"search": "2d162303-78bf-599e-b197-93590ac3d315", "search_extended": True})

        decorated_collection_rating = self.datasource_decorator.get_collection("Rating")
        with patch("forestadmin.datasource_toolkit.decorators.search.collections.ForestLogger.log") as log_method:
            returned_filter = self.loop.run_until_complete(
                decorated_collection_rating._refine_filter(self.mocked_caller, filter_)
            )
            log_method.assert_called_once_with(
                "debug",
                "We're not searching through Rating.target because it's a polymorphic relation. "
                "You can override the default search behavior with 'replace_search'. "
                "See more: https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/search",
            )

        self.assertEqual(
            returned_filter,
            Filter(
                {
                    "condition_tree": ConditionTreeBranch(
                        aggregator=Aggregator.OR,
                        conditions=[
                            ConditionTreeLeaf("id", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                            ConditionTreeLeaf("target_id", Operator.EQUAL, "2d162303-78bf-599e-b197-93590ac3d315"),
                        ],
                    ),
                    "search": None,
                    "search_extended": True,
                    "segment": None,
                }
            ),
        )

    def test_search_should_work_with_replacer(self):
        filter_ = Filter({"search": "something"})

        self.decorated_collection_person.replace_search(
            lambda value, extended, context: {  # returning as dict syntax is mandatory !!!
                "aggregator": Aggregator.AND,
                "conditions": [
                    {"field": "id", "operator": Operator.EQUAL, "value": context.caller.user_id},
                    {"field": "foo", "operator": Operator.EQUAL, "value": value},
                ],
            }
        )

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.AND,
                    [
                        ConditionTreeLeaf("id", Operator.EQUAL, 1),
                        ConditionTreeLeaf("foo", Operator.EQUAL, "something"),
                    ],
                ),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_replacer_fn_can_be_async(self):
        filter_ = Filter({"search": "something"})

        async def replacer_fn(value, extended, context):
            return {
                "aggregator": Aggregator.AND,
                "conditions": [
                    {"field": "id", "operator": Operator.EQUAL, "value": context.caller.user_id},
                    {"field": "foo", "operator": Operator.EQUAL, "value": value},
                ],
            }

        self.decorated_collection_person.replace_search(replacer_fn)

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.AND,
                    [
                        ConditionTreeLeaf("id", Operator.EQUAL, 1),
                        ConditionTreeLeaf("foo", Operator.EQUAL, "something"),
                    ],
                ),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_replacer_fn_can_return_condition_tree_as_object(self):
        filter_ = Filter({"search": "something"})

        async def replacer_fn(value, extended, context):
            return ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=context.caller.user_id),
                    ConditionTreeLeaf(field="foo", operator=Operator.EQUAL, value=value),
                ],
            )

        self.decorated_collection_person.replace_search(replacer_fn)

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_person._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    Aggregator.AND,
                    [
                        ConditionTreeLeaf("id", Operator.EQUAL, 1),
                        ConditionTreeLeaf("foo", Operator.EQUAL, "something"),
                    ],
                ),
                "search": None,
                "search_extended": None,
                "segment": None,
            }
        )

    def test_default_search_is_not_call_when_search_was_replaced(self):
        filter_ = Filter({"search": "something"})

        async def replacer_fn(value, extended, context):
            return ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=context.caller.user_id),
                    ConditionTreeLeaf(field="foo", operator=Operator.EQUAL, value=value),
                ],
            )

        spy_replacer_fn = AsyncMock(wraps=replacer_fn)
        self.decorated_collection_person.replace_search(spy_replacer_fn)

        with patch.object(
            self.decorated_collection_person,
            "_default_replacer",
            wraps=self.decorated_collection_person._default_replacer,
        ) as spy_default_replacer:
            self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
            spy_default_replacer.assert_not_called()
            spy_replacer_fn.assert_awaited_with("something", False, ANY)

    def test_extended_search_should_be_correctly_given_to_default_replacer(self):
        filter_ = Filter({"search": "something"})

        with patch.object(
            self.decorated_collection_person,
            "_default_replacer",
            wraps=self.decorated_collection_person._default_replacer,
        ) as spy_default_replacer:
            self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
            spy_default_replacer.assert_called_with("something", False)

        filter_ = Filter({"search": "something", "search_extended": True})
        with patch.object(
            self.decorated_collection_person,
            "_default_replacer",
            wraps=self.decorated_collection_person._default_replacer,
        ) as spy_default_replacer:
            self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
            spy_default_replacer.assert_called_with("something", True)

    def test_extended_search_should_be_correctly_given_to_override_replacer(self):
        async def replacer_fn(value, extended, context):
            return ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=context.caller.user_id),
                    ConditionTreeLeaf(field="foo", operator=Operator.EQUAL, value=value),
                ],
            )

        spy_replacer_fn = AsyncMock(wraps=replacer_fn)
        self.decorated_collection_person.replace_search(spy_replacer_fn)

        filter_ = Filter({"search": "something"})
        self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
        spy_replacer_fn.assert_awaited_with("something", False, ANY)

        filter_ = Filter({"search": "something", "search_extended": True})
        self.loop.run_until_complete(self.decorated_collection_person._refine_filter(self.mocked_caller, filter_))
        spy_replacer_fn.assert_awaited_with("something", True, ANY)

    def test_disable_search_should_mark_schema_as_dirty(self):
        with patch.object(self.decorated_collection_person, "mark_schema_as_dirty") as mark_schema_as_dirty:
            self.decorated_collection_person.disable_search()
            mark_schema_as_dirty.assert_called_once()

    def test_replace_search_should_mark_schema_as_dirty(self):
        with patch.object(self.decorated_collection_person, "mark_schema_as_dirty") as mark_schema_as_dirty:
            self.decorated_collection_person.replace_search(None)
            mark_schema_as_dirty.assert_called_once()
