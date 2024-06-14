import sys
from typing import Any, Callable, Dict, List, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from typing_extensions import NotRequired, TypedDict

ReplacerAlias = Callable[[ConditionTreeLeaf, zoneinfo.ZoneInfo], ConditionTree]


class Alternative(TypedDict):
    depends_on: List[Operator]
    replacer: ReplacerAlias
    for_types: NotRequired[List[PrimitiveType]]


def _blank_to_in(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override(
        {
            "operator": Operator.IN,
            "value": [None, ""],
        }
    )


def _blank_to_missing(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTreeLeaf:
    return leaf.override({"operator": Operator.MISSING})


def _missing_to_equal(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override({"operator": Operator.EQUAL, "value": None})


def _present_to_not_in(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override({"operator": Operator.NOT_IN, "value": [None, ""]})


def _present_to_not_equal(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override(
        {
            "operator": Operator.NOT_EQUAL,
            "value": None,
        }
    )


def _equal_to_in(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override({"operator": Operator.IN, "value": [leaf.value]})


def _in_to_equal(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    values = cast(List[Any], leaf.value)
    return ConditionTreeFactory.union([leaf.override({"operator": Operator.EQUAL, "value": item}) for item in values])


def _not_equal_to_not_in(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    return leaf.override({"operator": Operator.NOT_IN, "value": [leaf.value]})


def _not_in_to_not_equal(leaf: ConditionTreeLeaf, _: zoneinfo.ZoneInfo) -> ConditionTree:
    values = cast(List[Any], leaf.value)
    return ConditionTreeFactory.intersect(
        [leaf.override({"operator": Operator.NOT_EQUAL, "value": item}) for item in values]
    )


def equality_transforms() -> Dict[Operator, List[Alternative]]:
    return {
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
