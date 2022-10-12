from unittest import mock

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _blank_to_in,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _blank_to_missing,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _equal_to_in,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _in_to_equal,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _missing_to_equal,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _not_equal_to_not_in,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _not_in_to_not_equal,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _present_to_not_equal,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    _present_to_not_in,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import equality_transforms


def test_blank_to_in():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _blank_to_in(leaf, "") == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.IN, "value": [None, ""]})


def test_blank_to_missing():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _blank_to_missing(leaf, "") == "fake_override"
        mock_override.assert_called_once_with(
            {
                "operator": Operator.MISSING,
            }
        )


def test_present_to_not_in():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.PRESENT)
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _present_to_not_in(leaf, "") == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.NOT_IN, "value": [None, ""]})


def test_present_to_not_equal():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.PRESENT)
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _present_to_not_equal(leaf, "") == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.NOT_EQUAL, "value": None})


def test_equal_to_in():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value="leaf_value")
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _equal_to_in(leaf, "") == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.IN, "value": [leaf.value]})


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.ConditionTreeFactory.union")
def test_in_to_equal(mock_union: mock.MagicMock):
    leaf = ConditionTreeLeaf(field="test", operator=Operator.IN, value=["1", "2"])
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.side_effect = ["fake_override", "fake_override1"]
        mock_union.return_value = "fake_union"
        assert _in_to_equal(leaf, "") == "fake_union"
        mock_union.assert_called_once_with(["fake_override", "fake_override1"])
        mock_override.assert_has_calls(
            [
                mock.call({"operator": Operator.EQUAL, "value": "1"}),
                mock.call({"operator": Operator.EQUAL, "value": "2"}),
            ]
        )


def test_not_equal_to_in():
    leaf = ConditionTreeLeaf(field="test", operator=Operator.NOT_EQUAL, value="leaf_value")
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert _not_equal_to_not_in(leaf, "") == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.NOT_IN, "value": [leaf.value]})


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.ConditionTreeFactory.union")
def test_not_in_to_not_equal(mock_union: mock.MagicMock):
    leaf = ConditionTreeLeaf(field="test", operator=Operator.NOT_IN, value=["1", "2"])
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.side_effect = ["fake_override", "fake_override1"]
        mock_union.return_value = "fake_union"
        assert _not_in_to_not_equal(leaf, "") == "fake_union"
        mock_union.assert_called_once_with(["fake_override", "fake_override1"])
        mock_override.assert_has_calls(
            [
                mock.call({"operator": Operator.NOT_EQUAL, "value": "1"}),
                mock.call({"operator": Operator.NOT_EQUAL, "value": "2"}),
            ]
        )


def test_equality_transforms():
    assert equality_transforms() == {
        Operator.BLANK: [
            {
                "depends_on": [Operator.IN],
                "for_types": [PrimitiveType.STRING],
                "replacer": _blank_to_in,
            },
            {"depends_on": [Operator.MISSING], "replacer": _blank_to_missing},
        ],
        Operator.IN: [{"depends_on": [Operator.EQUAL], "replacer": _in_to_equal}],
        Operator.MISSING: [{"depends_on": [Operator.EQUAL], "replacer": _missing_to_equal}],
        Operator.PRESENT: [
            {
                "depends_on": [Operator.NOT_IN],
                "for_types": [PrimitiveType.STRING],
                "replacer": _present_to_not_in,
            },
            {"depends_on": [Operator.NOT_EQUAL], "replacer": _present_to_not_equal},
        ],
        Operator.EQUAL: [{"depends_on": [Operator.IN], "replacer": _equal_to_in}],
        Operator.NOT_EQUAL: [
            {
                "depends_on": [Operator.NOT_IN],
                "replacer": _not_equal_to_not_in,
            }
        ],
        Operator.NOT_IN: [
            {
                "depends_on": [Operator.NOT_EQUAL],
                "replacer": _not_in_to_not_equal,
            }
        ],
    }
