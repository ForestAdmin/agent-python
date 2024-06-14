# pyright: reportPrivateUsage=false
from unittest import mock

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence import ConditionTreeEquivalent
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import equality_transforms
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import pattern_transforms
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import time_transforms


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence.ConditionTreeEquivalent._get_replacer"
)
def test_get_equivalent_tree(get_replacer_mock: mock.Mock):
    leaf = ConditionTreeLeaf("id", Operator.EQUAL, 1)
    operators = {Operator.IN}
    column_type = PrimitiveType.NUMBER
    timezone = "UTC"

    get_replacer_mock.return_value = None
    assert ConditionTreeEquivalent.get_equivalent_tree(leaf, operators, column_type, timezone) is None
    get_replacer_mock.assert_called_once_with(leaf.operator, operators, column_type)

    get_replacer_mock.reset_mock()
    replacer_mock = mock.MagicMock(return_value="fake")
    get_replacer_mock.return_value = replacer_mock
    assert ConditionTreeEquivalent.get_equivalent_tree(leaf, operators, column_type, timezone) == "fake"
    get_replacer_mock.assert_called_once_with(leaf.operator, operators, column_type)
    replacer_mock.assert_called_once_with(leaf, timezone)


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence.ConditionTreeEquivalent._get_replacer"
)
def test_has_equivalent_tree(get_replacer_mock: mock.Mock):
    get_replacer_mock.return_value = None
    assert ConditionTreeEquivalent.has_equivalent_tree(Operator.EQUAL, {Operator.IN}, PrimitiveType.NUMBER) is False

    get_replacer_mock.return_value = "other value"
    assert ConditionTreeEquivalent.has_equivalent_tree(Operator.EQUAL, {Operator.IN}, PrimitiveType.NUMBER) is True


# Use mock is hard with recursive method
def test_get_replacer():
    assert ConditionTreeEquivalent._get_replacer(Operator.EQUAL, set(), PrimitiveType.STRING) is None
    assert ConditionTreeEquivalent._get_replacer(Operator.BLANK, {Operator.NOT_IN}, PrimitiveType.STRING) is None
    # Blank -> IN
    assert ConditionTreeEquivalent._get_replacer(Operator.BLANK, {Operator.IN}, PrimitiveType.STRING) is not None
    # BLANK -> MISSING -> EQUAL -> IN
    assert ConditionTreeEquivalent._get_replacer(Operator.BLANK, {Operator.IN}, PrimitiveType.NUMBER) is not None


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence.time_transforms", wraps=time_transforms
)
@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence.pattern_transforms",
    wraps=pattern_transforms,
)
@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence.equality_transforms",
    wraps=equality_transforms,
)
def test_get_alternatives(
    equality_transforms_mock: mock.Mock,
    pattern_transforms_mock: mock.Mock,
    time_transforms_mock: mock.Mock,
):
    ConditionTreeEquivalent._alternatives = {}

    assert ConditionTreeEquivalent._get_alternatives(Operator.EQUAL)[0]["depends_on"] == [Operator.IN]
    equality_transforms_mock.assert_called_once()
    pattern_transforms_mock.assert_called_once()
    time_transforms_mock.assert_called_once()

    assert (
        ConditionTreeEquivalent._alternatives.keys()
        == {
            **equality_transforms(),
            **pattern_transforms(),
            **time_transforms(),
        }.keys()
    )
    equality_transforms_mock.reset_mock()
    pattern_transforms_mock.reset_mock()
    time_transforms_mock.reset_mock()

    assert ConditionTreeEquivalent._get_alternatives(Operator.EQUAL)[0]["depends_on"] == [Operator.IN]
    equality_transforms_mock.assert_not_called()
    pattern_transforms_mock.assert_not_called()
    time_transforms_mock.assert_not_called()

    assert ConditionTreeEquivalent._get_alternatives(Operator.IN)[0]["depends_on"] == [Operator.EQUAL]
    equality_transforms_mock.assert_not_called()
    pattern_transforms_mock.assert_not_called()
    time_transforms_mock.assert_not_called()
