import sys
from typing import Any, Dict, Optional, Set

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class PermissionBody(TypedDict):
    actions: Set[str]
    actions_by_user: Dict[str, Set[int]]
    scopes: Dict[str, Any]


class Scope(TypedDict):
    condition_tree: ConditionTreeBranch
    dynamic_scope_values: Optional[Dict[Any, Any]]


class PermissionServiceException(BaseException):
    def __init__(self, message: str, status: int = 403):
        self.STATUS = status
        self.message = message
        super(PermissionServiceException, self).__init__(message)
