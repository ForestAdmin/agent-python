from typing import Any, Callable, Dict, List, cast

from typing_extensions import NotRequired, TypedDict

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)

ReplacerAlias = Callable[[ConditionTreeLeaf, str], ConditionTree]


class Alternative(TypedDict):
    depends_on: List[Operator]
    replacer: ReplacerAlias
    for_types: NotRequired[List[PrimitiveType]]


def __blank_to_in(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override(
        {
            "operator": Operator.IN,
            "value": [None, ""],
        }
    )


def __blank_to_missing(leaf: ConditionTreeLeaf, _: str) -> ConditionTreeLeaf:
    return leaf.override({"operator": Operator.MISSING})


def __missing_to_equal(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override({"operator": Operator.EQUAL, "value": None})


def __present_to_not_in(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override({"operator": Operator.NOT_IN, "value": [None, ""]})


def __present_to_not_equal(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override(
        {
            "operator": Operator.NOT_EQUAL,
            "value": None,
        }
    )


def __equal_to_in(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override({"operator": Operator.IN, "value": [leaf.value]})


def __in_to_equal(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    values = cast(List[Any], leaf.value)
    return ConditionTreeFactory.union([leaf.override({"operator": Operator.EQUAL, "value": item}) for item in values])


def __not_equal_to_not_in(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    return leaf.override({"operator": Operator.NOT_IN, "value": [leaf.value]})


def __not_in_to_not_equal(leaf: ConditionTreeLeaf, _: str) -> ConditionTree:
    values = cast(List[Any], leaf.value)
    return ConditionTreeFactory.union(
        [leaf.override({"operator": Operator.NOT_EQUAL, "value": item}) for item in values]
    )


def equality_transforms() -> Dict[Operator, List[Alternative]]:
    return {
        Operator.BLANK: [
            {
                "depends_on": [Operator.IN],
                "for_types": [PrimitiveType.STRING],
                "replacer": __blank_to_in,
            },
            {"depends_on": [Operator.MISSING], "replacer": __blank_to_missing},
        ],
        Operator.IN: [{"depends_on": [Operator.EQUAL], "replacer": __in_to_equal}],
        Operator.MISSING: [{"depends_on": [Operator.EQUAL], "replacer": __missing_to_equal}],
        Operator.PRESENT: [
            {
                "depends_on": [Operator.NOT_IN],
                "for_types": [PrimitiveType.STRING],
                "replacer": __present_to_not_in,
            },
            {"depends_on": [Operator.NOT_EQUAL], "replacer": __present_to_not_equal},
        ],
        Operator.EQUAL: [{"depends_on": [Operator.IN], "replacer": __equal_to_in}],
        Operator.NOT_EQUAL: [
            {
                "depends_on": [Operator.NOT_IN],
                "replacer": __not_equal_to_not_in,
            }
        ],
        Operator.NOT_IN: [
            {
                "depends_on": [Operator.NOT_EQUAL],
                "replacer": __not_in_to_not_equal,
            }
        ],
    }
