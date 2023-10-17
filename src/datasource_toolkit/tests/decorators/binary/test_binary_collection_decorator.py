import asyncio
import os
import sys
from base64 import b64encode
from unittest import TestCase
from unittest.mock import AsyncMock, patch

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.binary.collection import BinaryCollectionDecorator
from forestadmin.datasource_toolkit.decorators.binary.utils import bytes2hex, hex2bytes
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, ManyToOne, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, Aggregator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator as conditionTreeAggregator,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestBaseBinaryDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()

        Collection.__abstractmethods__ = set()  # to instantiate abstract class
        cls.collection_favorite = Collection("Favorite", cls.datasource)
        cls.collection_favorite.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.NUMBER,
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
        cls.datasource.add_collection(cls.collection_favorite)

        cls.collection_book = Collection("Book", cls.datasource)
        cls.collection_book.add_fields(
            {
                "id": Column(
                    column_type=PrimitiveType.BINARY,
                    is_primary_key=True,
                    type=FieldType.COLUMN,
                    validations=[
                        {"operator": Operator.LONGER_THAN, "value": 15},
                        {"operator": Operator.SHORTER_THAN, "value": 17},
                        {"operator": Operator.PRESENT},
                        {"operator": Operator.NOT_EQUAL, "value": bytes2hex(b"123456")},
                    ],
                ),
                "title": Column(
                    column_type=PrimitiveType.STRING,
                    filter_operators=set([]),
                    is_primary_key=False,
                    type=FieldType.COLUMN,
                ),
                "cover": Column(column_type=PrimitiveType.BINARY, type=FieldType.COLUMN),
            }
        )
        cls.datasource.add_collection(cls.collection_book)
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
        self.decorated_datasource = DatasourceDecorator(self.datasource, BinaryCollectionDecorator)
        self.decorated_collection_book = self.decorated_datasource.get_collection("Book")
        self.decorated_collection_favorite = self.decorated_datasource.get_collection("Favorite")

        self.decorated_collection_favorite.schema
        self.decorated_collection_book.schema


class TestSetBinaryMode(TestBaseBinaryDecorator):
    def test_set_binary_mode_should_throw_on_invalid_mode(self):
        self.assertRaisesRegex(
            ForestException,
            r"Invalid binary mode$",
            self.decorated_collection_book.set_binary_mode,
            "cover",
            "invalid",
        )

    def test_set_binary_mode_should_raise_if_field_does_not_exists(self):
        self.assertRaisesRegex(
            KeyError,
            r"'invalid'$",
            self.decorated_collection_book.set_binary_mode,
            "invalid",
            "hex",
        )

    def test_set_binary_mode_should_throw_if_field_is_not_binary(self):
        self.assertRaisesRegex(
            ForestException,
            r"Expected a binary field$",
            self.decorated_collection_book.set_binary_mode,
            "title",
            "hex",
        )

    def test_set_binary_mode_should_not_throw_if_field_is_binary(self):
        self.decorated_collection_book.set_binary_mode("cover", "hex")


class TestSchema(TestBaseBinaryDecorator):
    def test_favorite_schema_should_not_be_modified(self):
        self.assertEqual(self.decorated_collection_favorite.schema, self.collection_favorite.schema)

    def test_book_pk_should_be_rewritten_as_an_hex_str(self):
        id_schema = self.decorated_collection_book.schema["fields"]["id"]
        self.assertEqual(id_schema["is_primary_key"], True)
        self.assertEqual(id_schema["column_type"], PrimitiveType.STRING)
        self.assertEqual(
            id_schema["validations"],
            [
                {"operator": Operator.MATCH, "value": r"^[0-9a-f]+$"},
                {"operator": Operator.LONGER_THAN, "value": 31},
                {"operator": Operator.SHORTER_THAN, "value": 33},
                {"operator": Operator.PRESENT},
            ],
        )

    def test_book_cover_should_be_rewritten_as_data_uri(self):
        cover_schema = self.decorated_collection_book.schema["fields"]["cover"]

        self.assertEqual(cover_schema["column_type"], PrimitiveType.STRING)
        self.assertEqual(
            cover_schema["validations"],
            [
                {"operator": Operator.MATCH, "value": r"^data:.*;base64,.*"},
            ],
        )

    def test_if_requested_cover_should_be_rewritten_as_data_uri(self):
        self.decorated_collection_book.set_binary_mode("cover", "datauri")
        cover_schema = self.decorated_collection_book.schema["fields"]["cover"]

        self.assertEqual(cover_schema["column_type"], PrimitiveType.STRING)
        self.assertEqual(
            cover_schema["validations"],
            [
                {"operator": Operator.MATCH, "value": r"^data:.*;base64,.*"},
            ],
        )


class TestList(TestBaseBinaryDecorator):
    def test_list_with_simple_filter_should_transform_query(self):
        condition_tree = ConditionTreeLeaf("id", Operator.EQUAL, "30303030")
        filter_ = PaginatedFilter({"condition_tree": condition_tree})

        expected_condition_tree = ConditionTreeLeaf("id", Operator.EQUAL, hex2bytes("30303030"))

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[]) as mock_child_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, filter_, Projection("id", "cover"))
            )
            mock_child_list.assert_awaited_once()
            await_args = mock_child_list.await_args.args
            self.assertEqual(await_args[1].condition_tree.value, expected_condition_tree.value)

    def test_list_with_simple_filter_should_transform_records(self):
        condition_tree = ConditionTreeLeaf("id", Operator.EQUAL, "30303030")
        filter_ = PaginatedFilter({"condition_tree": condition_tree})

        with open(os.path.abspath(os.path.join(__file__, "..", "transparent.gif")), "rb") as fin:
            file_content = fin.read()

        async def mocked_list(caller, filter__, projection):
            return [{"id": hex2bytes("30303030"), "title": "Foundation", "cover": file_content}]

        with patch.object(
            self.collection_book, "list", new_callable=AsyncMock, side_effect=mocked_list
        ) as mock_child_list:
            records = self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, filter_, Projection("id", "cover"))
            )
            mock_child_list.assert_awaited_once()
            self.assertEqual(records[0]["id"], "30303030")
            self.assertEqual(records[0]["cover"], "data:image/gif;base64," + b64encode(file_content).decode("ascii"))

    def test_list_with_complex_filter_should_be_transform(self):
        condition_tree = ConditionTreeBranch(
            conditionTreeAggregator.OR,
            [
                ConditionTreeLeaf("id", Operator.EQUAL, "30303030"),
                ConditionTreeLeaf("id", Operator.IN, ["30303030"]),
                ConditionTreeLeaf("title", Operator.EQUAL, "Foundation"),
                ConditionTreeLeaf("title", Operator.LIKE, "Found%"),
                ConditionTreeLeaf("cover", Operator.EQUAL, b"data:image/gif;base64," + b64encode(b"123")),
            ],
        )
        filter_ = PaginatedFilter({"condition_tree": condition_tree})

        expected_condition_tree = ConditionTreeBranch(
            conditionTreeAggregator.OR,
            [
                ConditionTreeLeaf("id", Operator.EQUAL, hex2bytes("30303030")),
                ConditionTreeLeaf("id", Operator.IN, [hex2bytes("30303030")]),
                ConditionTreeLeaf("title", Operator.EQUAL, "Foundation"),
                ConditionTreeLeaf("title", Operator.LIKE, "Found%"),
                ConditionTreeLeaf("cover", Operator.EQUAL, b"123"),
            ],
        )

        with patch.object(self.collection_book, "list", new_callable=AsyncMock, return_value=[]) as mock_child_list:
            self.loop.run_until_complete(
                self.decorated_collection_book.list(self.mocked_caller, filter_, Projection("id", "cover"))
            )
            mock_child_list.assert_awaited_once()
            await_args = mock_child_list.await_args.args

            for i, condition in enumerate(await_args[1].condition_tree.conditions):
                if hasattr(condition.value, "read"):
                    self.assertEqual(condition.value.read(), expected_condition_tree.conditions[i].value)
                elif isinstance(condition.value, list) and hasattr(condition.value[0], "read"):
                    for j, v in enumerate(condition.value):
                        self.assertEqual(v.read(), expected_condition_tree.conditions[i].value[j])
                else:
                    self.assertEqual(condition.value, expected_condition_tree.conditions[i].value)

    def test_list_from_relation_should_transform_record_and_query(self):
        condition_tree = ConditionTreeLeaf("book:id", Operator.EQUAL, "30303030")
        filter_ = PaginatedFilter({"condition_tree": condition_tree})
        with open(os.path.abspath(os.path.join(__file__, "..", "transparent.gif")), "rb") as fin:
            file_content = fin.read()

        async def mocked_list(caller, filter__, projection):
            self.assertEqual(filter__.condition_tree.field, "book:id")
            self.assertEqual(filter__.condition_tree.value, hex2bytes("30303030"))
            return [
                {
                    "id": 2,
                    "book": {"id": hex2bytes("30303030"), "cover": file_content},
                }
            ]

        with patch.object(
            self.collection_favorite, "list", new_callable=AsyncMock, side_effect=mocked_list
        ) as mock_child_list:
            records = self.loop.run_until_complete(
                self.decorated_collection_favorite.list(
                    self.mocked_caller, filter_, Projection("book:id", "book:cover")
                )
            )
            mock_child_list.assert_awaited_once()
            self.assertEqual(records[0]["id"], 2)
            self.assertEqual(records[0]["book"]["id"], "30303030")
            self.assertEqual(
                records[0]["book"]["cover"], "data:image/gif;base64," + b64encode(file_content).decode("ascii")
            )


class TestCreate(TestBaseBinaryDecorator):
    def test_simple_creation_should_transform_record_for_database(self):
        record = {"id": "30303030", "cover": b"data:application/octet-stream;base64,aGVsbG8="}

        async def mock_create(caller, data):
            self.assertEqual(data[0]["id"], b"0000")
            self.assertEqual(data[0]["cover"], b"hello")
            return []

        with patch.object(
            self.collection_book, "create", new_callable=AsyncMock, side_effect=mock_create
        ) as mock_child_create:
            self.loop.run_until_complete(self.decorated_collection_book.create(self.mocked_caller, [record]))
            mock_child_create.assert_awaited_once()

    def test_simple_creation_should_transform_record_when_coming_from_database(self):
        record = {"id": "30303030", "cover": "data:application/octet-stream;base64,aGVsbG8="}

        async def mock_create(caller, data):
            return [{"id": b"0000", "cover": b"hello"}]

        with patch.object(
            self.collection_book, "create", new_callable=AsyncMock, side_effect=mock_create
        ) as mock_child_create:
            created = self.loop.run_until_complete(self.decorated_collection_book.create(self.mocked_caller, [record]))
            mock_child_create.assert_awaited_once()
            self.assertEqual(created[0], record)


class TestUpdate(TestBaseBinaryDecorator):
    def test_patch_should_be_transformed_for_db(self):
        patch_ = {"cover": "data:image/gif;base64,aGVsbG8="}

        async def mock_update(caller, filter, data):
            self.assertEqual(data["cover"], b"hello")

        with patch.object(
            self.collection_book, "update", new_callable=AsyncMock, side_effect=mock_update
        ) as mock_child_update:
            self.loop.run_until_complete(self.decorated_collection_book.update(self.mocked_caller, Filter({}), patch_))
            mock_child_update.assert_awaited_once()


class TestAggregate(TestBaseBinaryDecorator):
    def test_binary_groups_in_result_should_be_transform(self):
        async def mock_aggregate(caller, filter, aggregation, limit):
            return [{"value": 1, "group": {"cover": b"hello"}}]

        with patch.object(
            self.collection_book, "aggregate", new_callable=AsyncMock, side_effect=mock_aggregate
        ) as mock_child_aggregate:
            result = self.loop.run_until_complete(
                self.decorated_collection_book.aggregate(
                    self.mocked_caller,
                    Filter({}),
                    Aggregation({"field": "title", "operation": Aggregator.COUNT, "groups": [{"field": "cover"}]}),
                )
            )
            mock_child_aggregate.assert_awaited_once()
            self.assertEqual(
                result, [{"value": 1, "group": {"cover": "data:application/octet-stream;base64,aGVsbG8="}}]
            )

    def test_from_relation_binary_groups_in_result_should_be_transform(self):
        async def mock_aggregate(caller, filter, aggregation, limit):
            return [{"value": 1, "group": {"book:cover": b"hello"}}]

        with patch.object(
            self.collection_favorite, "aggregate", new_callable=AsyncMock, side_effect=mock_aggregate
        ) as mock_child_aggregate:
            result = self.loop.run_until_complete(
                self.decorated_collection_favorite.aggregate(
                    self.mocked_caller,
                    Filter({}),
                    Aggregation({"field": "id", "operation": Aggregator.COUNT, "groups": [{"field": "book:cover"}]}),
                )
            )
            mock_child_aggregate.assert_awaited_once()
            self.assertEqual(
                result, [{"value": 1, "group": {"book:cover": "data:application/octet-stream;base64,aGVsbG8="}}]
            )
