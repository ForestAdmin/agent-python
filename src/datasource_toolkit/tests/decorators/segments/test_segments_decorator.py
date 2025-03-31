import asyncio
import sys
from unittest import TestCase
from unittest.mock import patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.segments.collections import SegmentCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


class TestSegmentCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_product = Collection("Product", cls.datasource)
        cls.collection_product.add_fields(
            {
                "id": Column(column_type=PrimitiveType.NUMBER, is_primary_key=True, type=FieldType.COLUMN),
                "name": Column(column_type=PrimitiveType.STRING, type=FieldType.COLUMN),
                "price": Column(
                    column_type=PrimitiveType.NUMBER,
                    type=FieldType.COLUMN,
                ),
            }
        )

        cls.datasource.add_collection(cls.collection_product)
        cls.datasource_decorator = DatasourceDecorator(cls.datasource, SegmentCollectionDecorator)

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
        self.decorated_collection_product = self.datasource_decorator.get_collection("Product")

    def test_schema_segments_return_list_of_segments(self):
        self.decorated_collection_product.add_segment(
            "segment_name", lambda ctx: {"field": "price", "operator": Operator.GREATER_THAN, "value": 750}
        )
        self.decorated_collection_product.add_segment(
            "segment_name_2", lambda ctx: {"field": "price", "operator": Operator.LESS_THAN, "value": 1000}
        )

        assert len(self.decorated_collection_product.schema["segments"]) == 2
        assert "segment_name" in self.decorated_collection_product.schema["segments"]
        assert "segment_name_2" in self.decorated_collection_product.schema["segments"]

    def test_refine_filter_should_return_null_if_null_filter_is_given(self):
        self.decorated_collection_product.add_segment(
            "segment_name", lambda ctx: {"field": "price", "operator": Operator.GREATER_THAN, "value": 750}
        )
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_product._refine_filter(self.mocked_caller, None)
        )
        assert returned_filter is None

    def test_should_return_the_same_filter_if_segment_not_managed(self):
        self.decorated_collection_product.add_segment(
            "segment_name", lambda ctx: {"field": "price", "operator": Operator.GREATER_THAN, "value": 750}
        )
        filter_ = Filter({"segment": "a_segment"})

        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_product._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == filter_

    def test_tree_and_segment_should_be_merged_in_a_condition_tree(self):
        self.decorated_collection_product.add_segment(
            "segment_name",
            lambda ctx: ConditionTreeLeaf(**{"field": "name", "operator": Operator.EQUAL, "value": "a_name_value"}),
        )
        filter_ = Filter(
            {"segment": "segment_name", "condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "other_name_value")}
        )
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_product._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter(
            {
                "condition_tree": ConditionTreeBranch(
                    aggregator=Aggregator.AND,
                    conditions=[
                        ConditionTreeLeaf("name", Operator.EQUAL, "a_name_value"),
                        ConditionTreeLeaf("name", Operator.EQUAL, "other_name_value"),
                    ],
                )
            }
        )

    def test_segment_can_be_async_and_return_dict_condition_tree(self):
        async def segment_fn(context: CollectionCustomizationContext):
            return {"field": "name", "operator": Operator.EQUAL, "value": "a_name_value"}

        self.decorated_collection_product.add_segment("segment_name", segment_fn)
        filter_ = Filter({"segment": "segment_name"})
        returned_filter = self.loop.run_until_complete(
            self.decorated_collection_product._refine_filter(self.mocked_caller, filter_)
        )
        assert returned_filter == Filter({"condition_tree": ConditionTreeLeaf("name", Operator.EQUAL, "a_name_value")})

    def test_should_schema_should_contains_segments_define_in_custom_datasource(self):
        with patch.dict(self.collection_product._schema, {"segments": ["segment_test"]}):
            self.assertIn(
                "segment_test",
                self.decorated_collection_product.schema["segments"],
            )
