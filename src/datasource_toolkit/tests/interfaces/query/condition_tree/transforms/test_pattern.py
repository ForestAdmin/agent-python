import sys

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from unittest import mock

import pytest
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import (
    _contains_pattern,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import (
    _ends_with_pattern,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import (
    _like_replacer,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import (
    _starts_with_pattern,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import (
    PatternException,
    likes,
    pattern_transforms,
)


def test_like_replacer():
    get_pattern = mock.MagicMock(return_value="new_value")
    replacer = _like_replacer(get_pattern)

    leaf = ConditionTreeLeaf(field="test", operator=Operator.EQUAL, value=1)
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "new_leaf"
        assert replacer(leaf, zoneinfo.ZoneInfo("UTC")) == "new_leaf"
        mock_override.assert_called_once_with({"operator": Operator.LIKE, "value": "new_value"})
        get_pattern.assert_called_once_with(str(1))

    leaf = ConditionTreeLeaf(field="test", operator=Operator.BLANK)
    with pytest.raises(PatternException):
        replacer(leaf, zoneinfo.ZoneInfo("UTC"))


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern._like_replacer")
def test_likes(_like_replacer: mock.MagicMock):
    _like_replacer.return_value = "replacer"
    get_pattern = mock.MagicMock()
    assert likes(get_pattern) == {
        "depends_on": [Operator.LIKE],
        "for_types": [PrimitiveType.STRING],
        "replacer": "replacer",
    }
    _like_replacer.assert_called_once_with(get_pattern)


def test_contains_pattern():
    assert _contains_pattern("value") == "%value%"


def test_starts_with_pattern():
    assert _starts_with_pattern("value") == "value%"


def test_ends_with_pattern():
    assert _ends_with_pattern("value") == "%value"


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern.likes")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern._contains_pattern")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern._starts_with_pattern")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern._ends_with_pattern")
def test_pattern_transforms(
    ends_mock: mock.MagicMock, starts_mock: mock.MagicMock, contains_mock: mock.MagicMock, like_mock: mock.MagicMock
):
    like_mock.side_effect = ["fake_contains", "fake_starts", "fake_ends", "fake_like"]

    assert pattern_transforms() == {
        Operator.CONTAINS: ["fake_contains"],
        Operator.STARTS_WITH: ["fake_starts"],
        Operator.ENDS_WITH: ["fake_ends"],
        Operator.LIKE: ["fake_like"],
    }
    like_mock.assert_has_calls([mock.call(contains_mock), mock.call(starts_mock), mock.call(ends_mock)])
