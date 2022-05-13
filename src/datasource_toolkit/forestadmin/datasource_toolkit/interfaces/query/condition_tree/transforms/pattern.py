from typing import Callable, Dict, List

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    Alternative,
)


def likes(getPattern: Callable[[str], str]) -> Alternative:
    return {
        "depends_on": [Operator.LIKE],
        "for_types": [PrimitiveType.STRING],
        "replacer": lambda leaf, _: leaf.override(
            {
                "operator": Operator.LIKE,
                "value": getPattern(leaf.value),
            }
        ),
    }


def pattern_transforms() -> Dict[Operator, List[Alternative]]:
    return {
        Operator.CONTAINS: [likes(lambda value: f"%{value}%")],
        Operator.STARTS_WITH: [likes(lambda value: f"{value}%")],
        Operator.ENDS_WITH: [likes(lambda value: f"%{value}")],
    }
