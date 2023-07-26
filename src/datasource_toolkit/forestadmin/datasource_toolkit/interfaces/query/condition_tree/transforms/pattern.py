from typing import Any, Callable, Dict, List

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    Alternative,
    ReplacerAlias,
)


class PatternException(DatasourceToolkitException):
    pass


def _like_replacer(get_pattern: Callable[[str], str]) -> ReplacerAlias:
    def __replacer(leaf: ConditionTreeLeaf, _: Any):
        if not leaf.value:
            raise PatternException("Unable to use like with None value")
        return leaf.override(
            {
                "operator": Operator.LIKE,
                "value": get_pattern(str(leaf.value)),
            }
        )

    return __replacer


def likes(get_pattern: Callable[[str], str]) -> Alternative:
    return {"depends_on": [Operator.LIKE], "for_types": [PrimitiveType.STRING], "replacer": _like_replacer(get_pattern)}


def _contains_pattern(value: str) -> str:
    return f"%{value}%"


def _starts_with_pattern(value: str) -> str:
    return f"{value}%"


def _ends_with_pattern(value: str) -> str:
    return f"%{value}"


def _like_pattern(value: str) -> str:
    return f"{value}"


def pattern_transforms() -> Dict[Operator, List[Alternative]]:
    return {
        Operator.CONTAINS: [likes(_contains_pattern)],
        Operator.STARTS_WITH: [likes(_starts_with_pattern)],
        Operator.ENDS_WITH: [likes(_ends_with_pattern)],
        Operator.LIKE: [likes(_like_pattern)],
    }
