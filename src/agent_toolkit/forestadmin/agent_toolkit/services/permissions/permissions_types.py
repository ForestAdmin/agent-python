from typing import Any, Dict, Optional, Set, TypedDict

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch


class PermissionBody(TypedDict):
    actions: Set[str]
    actions_by_user: Dict[str, Set[int]]
    scopes: Dict[str, Any]


class Scope(TypedDict):
    condition_tree: ConditionTreeBranch
    dynamic_scope_values: Optional[Dict[Any, Any]]
