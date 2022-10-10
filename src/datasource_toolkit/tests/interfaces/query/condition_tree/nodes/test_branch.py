import sys

if sys.version_info < (3, 8):
    from mock import AsyncMock
else:
    from unittest.mock import AsyncMock

from unittest import mock
from unittest.mock import MagicMock

import pytest
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTreeException
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator,
    BranchComponents,
    ConditionTreeBranch,
    is_branch_component,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf, LeafComponents
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def test_is_branc_component():

    tree = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    assert is_branch_component(tree) is False

    component = LeafComponents(field="test", operator="blank")
    assert is_branch_component(component) is False

    tree = ConditionTreeBranch(aggregator=Aggregator.AND, conditions=[])
    assert is_branch_component(tree) is False

    component = BranchComponents(aggregator="and", conditions=[])
    assert is_branch_component(component)


def test_condition_tree_branch_constructor():

    tree = ConditionTreeBranch(Aggregator.AND, [ConditionTreeBranch(Aggregator.OR, [])])
    assert tree.aggregator == Aggregator.AND
    assert tree.conditions == [ConditionTreeBranch(Aggregator.OR, [])]


def test_condition_tree_branch_equality():

    tree = ConditionTreeBranch(Aggregator.AND, [ConditionTreeBranch(Aggregator.OR, [])])
    tree1 = ConditionTreeBranch(Aggregator.AND, [ConditionTreeBranch(Aggregator.OR, [])])

    assert tree == tree1

    tree.aggregator = Aggregator.OR
    assert tree != tree1

    tree.aggregator = Aggregator.AND
    tree.conditions = []
    assert tree != tree1

    tree.aggregator = Aggregator.OR
    assert tree != tree1


def test_projection():

    tree = ConditionTreeBranch(
        Aggregator.AND,
        [
            ConditionTreeBranch(
                Aggregator.OR,
                [ConditionTreeLeaf("test", Operator.BLANK), ConditionTreeLeaf("test1", Operator.NOT_EQUAL, 1)],
            ),
            ConditionTreeLeaf("test2", Operator.BLANK),
        ],
    )
    assert tree.projection == Projection("test", "test1", "test2")


def test_inverse():
    tree = ConditionTreeBranch(Aggregator.OR, conditions=[])
    assert tree.inverse() == ConditionTreeBranch(Aggregator.AND, conditions=[])

    tree = ConditionTreeBranch(Aggregator.AND, conditions=[])
    assert tree.inverse() == ConditionTreeBranch(Aggregator.OR, conditions=[])


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch.all")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch.any")
def test_match(mock_any: mock.MagicMock, mock_all: mock.MagicMock):

    record: RecordsDataAlias = mock.MagicMock()
    collection: Collection = mock.MagicMock()
    timezone: str = "UTC"

    condition = MagicMock()
    condition.match = MagicMock(return_value="match_condition")

    condition1 = MagicMock()
    condition1.match = MagicMock(return_value="match_condition1")

    mock_any.return_value = "any"
    mock_all.return_value = "all"

    tree = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[condition, condition1])
    res = tree.match(record, collection, timezone)
    assert res == "any"
    mock_all.assert_not_called()
    mock_any.assert_called_once_with(["match_condition", "match_condition1"])
    condition.match.assert_called_once_with(record, collection, timezone)  # type: ignore
    condition1.match.assert_called_once_with(record, collection, timezone)  # type: ignore

    mock_any.reset_mock()
    condition.match.reset_mock()  # type: ignore
    condition1.match.reset_mock()  # type: ignore

    tree = ConditionTreeBranch(aggregator=Aggregator.AND, conditions=[condition, condition1])
    res = tree.match(record, collection, timezone)
    assert res == "all"
    mock_any.assert_not_called()
    mock_all.assert_called_once_with(["match_condition", "match_condition1"])
    condition.match.assert_called_once_with(record, collection, timezone)  # type: ignore
    condition1.match.assert_called_once_with(record, collection, timezone)  # type: ignore


def test_apply():

    handler = mock.MagicMock()
    condition = MagicMock()
    condition.apply = MagicMock()

    condition1 = MagicMock()
    condition1.apply = MagicMock()
    tree = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[condition, condition1])

    tree.apply(handler)
    condition.apply.assert_called_once_with(handler)  # type: ignore
    condition1.apply.assert_called_once_with(handler)  # type: ignore


def test_replace():
    handler = mock.MagicMock()
    condition = MagicMock()
    new_condition = MagicMock()
    condition.replace = MagicMock(return_value=new_condition)

    condition1 = MagicMock()
    new_condition1 = MagicMock()
    condition1.replace = MagicMock(return_value=new_condition1)

    tree = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[condition, condition1])

    assert tree.replace(handler) == ConditionTreeBranch(
        aggregator=Aggregator.OR, conditions=[new_condition, new_condition1]
    )
    condition.replace.assert_called_once_with(handler)  # type: ignore
    condition1.replace.assert_called_once_with(handler)  # type: ignore


@pytest.mark.asyncio
async def test_replace_async():
    handler = mock.MagicMock()
    condition = MagicMock()
    new_condition = MagicMock()
    condition.replace_async = AsyncMock(return_value=new_condition)

    condition1 = MagicMock()
    new_condition1 = MagicMock()
    condition1.replace_async = AsyncMock(return_value=new_condition1)

    tree = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[condition, condition1])
    assert await tree.replace_async(handler) == ConditionTreeBranch(
        aggregator=Aggregator.OR, conditions=[new_condition, new_condition1]
    )
    condition.replace_async.assert_called_once_with(handler)  # type: ignore
    condition1.replace_async.assert_called_once_with(handler)  # type: ignore


def test_nest():
    prefix = "prefix"

    condition = MagicMock()
    nest_condition = MagicMock()
    condition.nest = MagicMock(return_value=nest_condition)

    condition1 = MagicMock()
    nest_condition1 = MagicMock()
    condition1.nest = MagicMock(return_value=nest_condition1)

    tree = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[condition, condition1])
    assert tree.nest(prefix) == ConditionTreeBranch(
        aggregator=Aggregator.OR, conditions=[nest_condition, nest_condition1]
    )


# unable to mock this method
def test_get_prefix():

    leaf1 = ConditionTreeLeaf(field="prefix:field", operator=Operator.BLANK)
    leaf2 = ConditionTreeLeaf(field="prefix:field2", operator=Operator.BLANK)

    branch = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[leaf1, leaf2])
    assert branch._get_prefix() == "prefix"  # type: ignore

    leaf1 = ConditionTreeLeaf(field="sub_prefix:prefix:field", operator=Operator.BLANK)
    leaf2 = ConditionTreeLeaf(field="sub_prefix:prefix:field2", operator=Operator.BLANK)

    branch = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[leaf1, leaf2])
    assert branch._get_prefix() == "sub_prefix"  # type: ignore

    leaf1 = ConditionTreeLeaf(field="prefix:field", operator=Operator.BLANK)
    leaf2 = ConditionTreeLeaf(field="different_prefix:field2", operator=Operator.BLANK)
    branch = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[leaf1, leaf2])
    with pytest.raises(ConditionTreeException):
        branch._get_prefix()  # type: ignore


# unable to mock this method
def test_remove_prefix():
    leaf1 = ConditionTreeLeaf(field="prefix:field", operator=Operator.BLANK)
    new_leaf1 = ConditionTreeLeaf(field="field", operator=Operator.BLANK)
    leaf2 = ConditionTreeLeaf(field="prefix:field2", operator=Operator.BLANK)
    new_leaf2 = ConditionTreeLeaf(field="field2", operator=Operator.BLANK)

    branch = ConditionTreeBranch(aggregator=Aggregator.OR, conditions=[leaf1, leaf2])
    assert branch._remove_prefix("prefix") == ConditionTreeBranch(  # type: ignore
        aggregator=Aggregator.OR, conditions=[new_leaf1, new_leaf2]
    )


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch.ConditionTreeBranch._get_prefix"
)
@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch.ConditionTreeBranch._remove_prefix"
)
def test_unnest(mock_remove_prefix: MagicMock, mock_get_prefix: MagicMock):
    mock_get_prefix.return_value = "fake_prefix"
    mock_remove_prefix.return_value = "unnest_tree"
    tree = ConditionTreeBranch(Aggregator.OR, [])
    assert tree.unnest() == "unnest_tree"
    mock_get_prefix.assert_called_once()
    mock_remove_prefix.assert_called_once_with("fake_prefix")
