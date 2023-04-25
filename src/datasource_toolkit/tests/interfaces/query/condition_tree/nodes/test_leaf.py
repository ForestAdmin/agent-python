import sys

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

from unittest import mock

import pytest
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import CallbackAlias, ReplacerAlias
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator,
    BranchComponents,
    ConditionTreeBranch,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
    ConditionTreeLeafException,
    LeafComponents,
    is_leaf_component,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def test_is_leaf_component():
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert is_leaf_component(tree) is False

    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")
    assert is_leaf_component(tree) is False

    tree = ConditionTreeBranch(aggregator=Aggregator.AND, conditions=[])
    assert is_leaf_component(tree) is False

    tree = BranchComponents(aggregator="and", conditions=[])
    assert is_leaf_component(tree) is False

    tree = LeafComponents(field="test", operator="blank")
    assert is_leaf_component(tree)

    tree = LeafComponents(field="test", operator="equal", value="1")
    assert is_leaf_component(tree)


def test_condition_tree_leaf_constructor():
    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")
    assert tree.field == "test"
    assert tree.operator == Operator.EQUAL
    assert tree.value == "1"


def test_condition_tree_leaf_equality():
    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")
    tree1 = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")

    assert tree == tree1

    tree.field = "test1"
    assert tree != tree1

    tree1.field = "test"
    tree1.operator = Operator.ENDS_WITH
    assert tree != tree1

    tree.operator = Operator.ENDS_WITH
    tree.value = "2"
    assert tree != tree1


def test_condition_tree_leaf_load():
    tree = LeafComponents(field="test", operator="blank")
    assert ConditionTreeLeaf.load(tree) == ConditionTreeLeaf(field="test", operator=Operator.BLANK)

    tree = LeafComponents(field="test", operator="equal", value="1")
    assert ConditionTreeLeaf.load(tree) == ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")


def test_condition_tree_projection():
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree.projection == Projection("test")


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf.override")
def test_condition_tree_leaf_inverse(mock_override: mock.Mock):
    tree = ConditionTreeLeaf(field="test", operator=Operator.PRESENT)
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.BLANK})
    mock_override.reset_mock()

    tree.operator = Operator.BLANK
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.PRESENT})
    mock_override.reset_mock()

    tree.operator = Operator.EQUAL
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.NOT_EQUAL})
    mock_override.reset_mock()

    tree.operator = Operator.IN
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.NOT_IN})
    mock_override.reset_mock()

    tree.operator = Operator.CONTAINS
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.NOT_CONTAINS})
    mock_override.reset_mock()

    tree.operator = Operator.NOT_EQUAL
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.EQUAL})
    mock_override.reset_mock()

    tree.operator = Operator.NOT_IN
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.IN})
    mock_override.reset_mock()

    tree.operator = Operator.NOT_CONTAINS
    tree.inverse()
    mock_override.assert_called_once_with({"operator": Operator.CONTAINS})
    mock_override.reset_mock()


@pytest.mark.parametrize(
    "operator",
    (
        Operator.LESS_THAN,
        Operator.GREATER_THAN,
        Operator.LIKE,
        Operator.STARTS_WITH,
        Operator.ENDS_WITH,
        Operator.LONGER_THAN,
        Operator.SHORTER_THAN,
        Operator.BEFORE,
        Operator.AFTER,
        Operator.AFTER_X_HOURS_AGO,
        Operator.BEFORE_X_HOURS_AGO,
        Operator.FUTURE,
        Operator.PAST,
        Operator.PREVIOUS_MONTH_TO_DATE,
        Operator.PREVIOUS_MONTH,
        Operator.PREVIOUS_QUARTER,
        Operator.PREVIOUS_QUARTER_TO_DATE,
        Operator.PREVIOUS_WEEK,
        Operator.PREVIOUS_WEEK_TO_DATE,
        Operator.PREVIOUS_X_DAYS,
        Operator.PREVIOUS_X_DAYS_TO_DATE,
        Operator.PREVIOUS_YEAR,
        Operator.PREVIOUS_YEAR_TO_DATE,
        Operator.TODAY,
        Operator.YESTERDAY,
        Operator.INCLUDES_ALL,
    ),
)
def test_condition_tree_leaf_inverse_exception(operator: Operator):
    tree = ConditionTreeLeaf(field="test", operator=operator)
    with pytest.raises(ConditionTreeLeafException) as e:
        tree.inverse()
    assert str(e.value) == f"🌳🌳🌳Operator '{operator}' cannot be inverted."


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf.load")
def test_condition_tree_leaf_handle_replace_tree(mock_load: mock.Mock):
    mock_load.return_value = "fake"
    tree = LeafComponents(field="test", operator="blank")
    replaced_tree = ConditionTreeLeaf._handle_replace_tree(tree)  # type: ignore
    mock_load.assert_called_once_with(tree)
    assert replaced_tree == "fake"
    mock_load.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    replaced_tree = ConditionTreeLeaf._handle_replace_tree(tree)  # type: ignore
    assert replaced_tree == tree
    mock_load.assert_not_called()


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf._handle_replace_tree"
)
def test_condition_tree_leaf_replace(mock_handle_replace_tree: mock.Mock):
    mock_handle_replace_tree.return_value = "fake"
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    replacer: ReplacerAlias = mock.MagicMock()
    replacer.return_value = "replacer_value"

    assert tree.replace(replacer) == "fake"
    replacer.assert_called_once_with(tree)
    mock_handle_replace_tree.assert_called_once_with("replacer_value")


@pytest.mark.asyncio
async def test_condition_tree_leaf_aync_replace():
    # @mock.patch doesn't work with mark.asyncio so we use context
    with mock.patch(
        "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf._handle_replace_tr"
        "ee"
    ) as mock_handle_replace_tree:
        mock_handle_replace_tree.return_value = "fake"
        tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
        replacer: ReplacerAlias = AsyncMock(return_value="replacer_value")

        assert await tree.replace_async(replacer) == "fake"
        replacer.assert_called_once_with(tree)
        mock_handle_replace_tree.assert_called_once_with("replacer_value")


def test__condition_tree_leaf_apply():
    handler: CallbackAlias = mock.MagicMock(return_value="fake")
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree.apply(handler) == "fake"
    handler.assert_called_once_with(tree)


def test_condition_tree_leaf_to_leaf_component():
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree._to_leaf_components == LeafComponents(field="test", operator="blank", value=None)  # type: ignore

    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="1")
    assert tree._to_leaf_components == LeafComponents(field="test", operator="equal", value="1")  # type: ignore


def test_condition_tree_leaf_override():
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree.override({"field": "override_field"}) == ConditionTreeLeaf(
        field="override_field",
        operator=Operator.BLANK,
        value=None,
    )

    assert tree.override({"operator": Operator.EQUAL}) == ConditionTreeLeaf(
        field="test",
        operator=Operator.EQUAL,
        value=None,
    )

    assert tree.override({"value": 1}) == ConditionTreeLeaf(
        field="test",
        operator=Operator.BLANK,
        value=1,
    )


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf.override")
def test_condition_tree_leaf_replace_field(mock_override: mock.MagicMock):
    mock_override.return_value = "fake"
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree.replace_field("new_field") == "fake"
    mock_override.assert_called_once_with({"field": "new_field"})


def test_condition_tree_leaf_equal():
    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value=1)
    assert tree._equal(1) is True  # type: ignore
    assert tree._equal(2) is False  # type: ignore


def test_condition_tree_leaf_verify_number_values():
    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value=1)
    tree._verify_is_number_values(1)  # type: ignore
    tree._verify_is_number_values(1.1)  # type: ignore

    tree.value = 1.1
    tree._verify_is_number_values(1)  # type: ignore
    tree._verify_is_number_values(1.1)  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree._verify_is_number_values("a")  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "&"
        tree._verify_is_number_values(1)  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "&"
        tree._verify_is_number_values("a")  # type: ignore


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes"
    ".leaf.ConditionTreeLeaf._verify_is_number_values"
)
def test_condition_tree_leaf_less_than(mock_verify_number: mock.Mock):
    tree = ConditionTreeLeaf(field="test", operator=Operator.LESS_THAN, value=1)
    assert tree._less_than(0) is True  # type: ignore
    assert tree._less_than(1) is False  # type: ignore
    assert tree._less_than(2) is False  # type: ignore

    mock_verify_number.side_effect = [ConditionTreeLeafException]
    with pytest.raises(ConditionTreeLeafException):
        tree._less_than("0")  # type: ignore


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes"
    ".leaf.ConditionTreeLeaf._verify_is_number_values"
)
def test_condition_tree_leaf_greater_than(mock_verify_number: mock.Mock):
    tree = ConditionTreeLeaf(field="test", operator=Operator.GREATER_THAN, value=1)
    assert tree._greater_than(2) is True  # type: ignore
    assert tree._greater_than(1) is False  # type: ignore
    assert tree._greater_than(0) is False  # type: ignore

    mock_verify_number.side_effect = [ConditionTreeLeafException]
    with pytest.raises(ConditionTreeLeafException):
        tree._greater_than("0")  # type: ignore


def test_condition_tree_leaf_longer_than():
    tree = ConditionTreeLeaf(field="test", operator=Operator.LONGER_THAN, value=1)
    assert tree._longer_than("aa") is True  # type: ignore
    assert tree._longer_than("") is False  # type: ignore
    assert tree._longer_than("a") is False  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree._longer_than(1)  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "a"
        tree._longer_than("a")  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "a"
        tree._longer_than(1)  # type: ignore


def test_condition_tree_leaf_shorter_than():
    tree = ConditionTreeLeaf(field="test", operator=Operator.LONGER_THAN, value=1)
    assert tree._shorter_than("") is True  # type: ignore
    assert tree._shorter_than("aa") is False  # type: ignore
    assert tree._shorter_than("a") is False  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree._shorter_than(1)  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "a"
        tree._shorter_than("a")  # type: ignore

    with pytest.raises(ConditionTreeLeafException):
        tree.value = "a"
        tree._shorter_than(1)  # type: ignore


def test_condition_tree_leaf_not_equal_not_contains():
    record: RecordsDataAlias = {}
    collection: Collection = mock.MagicMock()
    timezone = "UTC"
    tree = ConditionTreeLeaf(field="test", operator=Operator.NOT_CONTAINS, value="a")
    inversed_tree = mock.MagicMock(name="toto")
    inversed_tree.match = mock.MagicMock(name="tutu", return_value=False)
    inverse_mock = mock.MagicMock(return_value=inversed_tree)
    with mock.patch.object(tree, "inverse", inverse_mock):
        res = tree._not_equal_not_contains(record, collection, timezone)  # type: ignore
        assert res("value") is True
        inverse_mock.assert_called_once()
        inversed_tree.match.assert_called_once_with(record, collection, timezone)  # type: ignore


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.RecordUtils.get_field_value")
def test_simple_condition_tree_leaf_match(mock_get_field_value: mock.Mock):
    record: RecordsDataAlias = {}
    collection: Collection = mock.MagicMock()
    timezone = "UTC"
    mock_get_field_value.return_value = "fake_field_value"
    m = mock.MagicMock(return_value="fake_res")

    tree = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value=1)
    with mock.patch.object(tree, "_equal", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.LESS_THAN, value=1)
    with mock.patch.object(tree, "_less_than", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.GREATER_THAN, value=1)
    with mock.patch.object(tree, "_greater_than", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.LIKE, value=1)
    with mock.patch.object(tree, "_like", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.LONGER_THAN, value=1)
    with mock.patch.object(tree, "_longer_than", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.SHORTER_THAN, value=1)
    with mock.patch.object(tree, "_shorter_than", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    tree = ConditionTreeLeaf(field="test", operator=Operator.INCLUDES_ALL, value=1)
    with mock.patch.object(tree, "_includes_all", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with("fake_field_value")

    m.reset_mock()
    mock_get_field_value.reset_mock()

    _m = mock.MagicMock(return_value="fake_res")
    m = mock.MagicMock(return_value=_m)

    tree = ConditionTreeLeaf(field="test", operator=Operator.NOT_CONTAINS, value=1)
    with mock.patch.object(tree, "_not_equal_not_contains", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with(record, collection, timezone)
        _m.assert_called_once_with("fake_field_value")

    _m.reset_mock()
    m.reset_mock()
    mock_get_field_value.reset_mock()

    _m = mock.MagicMock(return_value="fake_res")
    m = mock.MagicMock(return_value=_m)

    tree = ConditionTreeLeaf(field="test", operator=Operator.NOT_EQUAL, value=1)
    with mock.patch.object(tree, "_not_equal_not_contains", m):
        assert tree.match(record, collection, timezone) == "fake_res"
        mock_get_field_value.assert_called_once_with(record, "test")
        m.assert_called_once_with(record, collection, timezone)
        _m.assert_called_once_with("fake_field_value")

    _m.reset_mock()
    m.reset_mock()
    mock_get_field_value.reset_mock()


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf.override")
def test_condition_tree_leaf_unnest(mock_override: mock.MagicMock):
    mock_override.return_value = ConditionTreeLeaf(field="subtest", operator=Operator.BLANK)
    tree = ConditionTreeLeaf(field="test:subtest", operator=Operator.BLANK)
    assert tree.unnest() == ConditionTreeLeaf(field="subtest", operator=Operator.BLANK)
    mock_override.assert_called_once_with({"field": "subtest"})

    mock_override.reset_mock()
    mock_override.return_value = ConditionTreeLeaf(field="test:subtest", operator=Operator.BLANK)
    tree = ConditionTreeLeaf(field="test1:test:subtest", operator=Operator.BLANK)
    assert tree.unnest() == ConditionTreeLeaf(field="test:subtest", operator=Operator.BLANK)
    mock_override.assert_called_once_with({"field": "test:subtest"})

    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    with pytest.raises(ConditionTreeLeafException):
        tree.unnest()


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf.ConditionTreeLeaf.override")
def test_condition_tree_leaf_nest(mock_override: mock.MagicMock):
    mock_override.return_value = ConditionTreeLeaf(field="prefix:test", operator=Operator.BLANK)
    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert tree.nest("prefix") == ConditionTreeLeaf(field="prefix:test", operator=Operator.BLANK)
    mock_override.assert_called_once_with({"field": "prefix:test"})
    with pytest.raises(ConditionTreeLeafException):
        tree.nest("")


def test_includes_all():
    tree = ConditionTreeLeaf(field="test", operator=Operator.IN, value=[1, 2, 3])
    assert tree._includes_all([1, 2])  # type:  ignore
    assert tree._includes_all([1, 2, 3])  # type:  ignore

    assert tree._includes_all([1, 2, 3, 4]) is False  # type:  ignore
    assert tree._includes_all([5]) is False  # type:  ignore


def test_like():
    tree = ConditionTreeLeaf(field="test", operator=Operator.LIKE, value="%t_s%zz")
    assert tree._like("tessdzz")  # type: ignore
    assert tree._like("stcszz")  # type: ignore
    assert tree._like("taszz")  # type: ignore
    assert tree._like("%t_s%zz")  # type: ignore

    assert tree._like("tsaaazz") is False  # type: ignore
    assert tree._like("tssaaaz") is False  # type: ignore
