import sys
from typing import Callable, Dict, List, Optional, Set, Union, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
    ConditionTreeComponent,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    Alternative,
    equality_transforms,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.pattern import pattern_transforms
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import time_transforms
from typing_extensions import TypeGuard

Replacer = Callable[[ConditionTreeLeaf, zoneinfo.ZoneInfo], ConditionTree]


class ConditionTreeEquivalentException(DatasourceToolkitException):
    pass


class ConditionTreeEquivalent:
    _alternatives: Dict[Operator, List[Alternative]] = {}

    @classmethod
    def get_equivalent_tree(
        cls,
        leaf: ConditionTreeLeaf,
        operators: Set[Operator],
        column_type: ColumnAlias,
        timezone: zoneinfo.ZoneInfo,
    ) -> Optional[ConditionTree]:
        replacer = cls._get_replacer(
            leaf.operator,
            operators,
            column_type,
        )
        if replacer:
            return replacer(leaf, timezone)

        return None

    @classmethod
    def has_equivalent_tree(cls, operator: Operator, operators: Set[Operator], column_type: ColumnAlias) -> bool:
        try:
            return cls._get_replacer(operator, operators, column_type) is not None
        except ConditionTreeEquivalentException:
            return False

    @classmethod
    def _get_replacer(
        cls,
        operator: Operator,
        allowed_operators: Set[Operator],
        column_type: ColumnAlias,
        visited: Optional[List[Alternative]] = None,
    ) -> Optional[Replacer]:
        if not visited:
            visited = []

        if operator in allowed_operators:
            return lambda leaf, tz: leaf

        for alternative in cls._get_alternatives(operator):
            for_types = alternative.get("for_types", [])
            is_valid_type = not for_types or column_type in for_types
            is_alternative_in_path = alternative in visited

            if is_valid_type and not is_alternative_in_path:
                depends_on_replacers: List[Optional[Replacer]] = []
                for replacement in alternative["depends_on"]:
                    depends_on_replacers.append(
                        cls._get_replacer(
                            replacement,
                            allowed_operators,
                            column_type,
                            [*visited, alternative],
                        )
                    )
                if cls.__is_complete(depends_on_replacers):
                    return cls.__apply_replacers(alternative, depends_on_replacers)
        return None

    @classmethod
    def _get_alternatives(cls, operator: Operator) -> List[Alternative]:
        if not cls._alternatives:
            cls._alternatives = {
                **equality_transforms(),
                **pattern_transforms(),
                **time_transforms(),
            }
        return cls._alternatives.get(operator, [])

    @staticmethod
    def __apply_replacers(alternative: Alternative, replacers: List[Replacer]):
        def __apply_replacer(tree: ConditionTreeLeaf, timezone: zoneinfo.ZoneInfo) -> ConditionTree:
            alternative_tree = alternative["replacer"](tree, timezone)

            def __replace(
                subtree: ConditionTree,
            ) -> Union[ConditionTree, ConditionTreeComponent]:
                subtree = cast(ConditionTreeLeaf, subtree)
                replacer = replacers[alternative["depends_on"].index(subtree.operator)]
                return replacer(subtree, timezone)

            res = alternative_tree.replace(__replace)
            return res

        return __apply_replacer

    @classmethod
    def __is_complete(cls, replacers_graph: List[Optional[Replacer]]) -> TypeGuard[List[Replacer]]:
        return len(replacers_graph) > 0 and all(replacers_graph)
