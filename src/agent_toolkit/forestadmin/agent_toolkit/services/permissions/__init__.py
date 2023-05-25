import itertools
import json
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from cachetools import TTLCache
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestRelationCollection
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.utils.context import Response, User
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


class PermissionBody(TypedDict):
    actions: Set[str]
    actions_by_user: Dict[str, Set[int]]
    scopes: Dict[str, Any]


def decode_permission_body(rendering_id: int, body: Dict[str, Any]) -> PermissionBody:
    if not body["meta"].get("rolesACLActivated"):
        raise PermissionServiceException("Roles V2 are unsupported")

    collections: Dict[str, Any] = {}
    stats: Dict[str, Any] = body.get("stats", {})
    renderings: Dict[str, Any] = {}

    if "data" in body:
        if body["data"].get("collections"):
            collections = body["data"]["collections"]

        renderings = body["data"].get("renderings", {})
        if str(rendering_id) in renderings:
            renderings = renderings[str(rendering_id)]
    actions, actions_by_user = _decode_action_permissions(collections)
    actions.update(_decode_chart_permissions(stats))

    scopes = _decode_scopes(renderings)

    return {"actions": actions, "actions_by_user": actions_by_user, "scopes": scopes}


class Scope(TypedDict):
    condition_tree: ConditionTreeBranch
    dynamic_scope_values: Optional[Dict[Any, Any]]


def _decode_scopes(rendering: Dict[str, Any]):
    scopes: Dict[str, Scope] = {}
    for name, v in rendering.items():
        if v.get("scope"):
            scopes[name] = {
                **v["scope"],
                "condition_tree": cast(
                    ConditionTreeBranch, ConditionTreeFactory.from_plain_object(v["scope"]["filter"])
                ),
                "dynamic_scope_values": v["scope"]["dynamicScopesValues"].get("users", {}),
            }
    return scopes


def _decode_action_permissions(collections: Dict[str, Any]) -> Tuple[Set[str], Dict[str, Set[int]]]:
    actions: Set[str] = set()
    actions_by_user: Dict[str, Set[int]] = {}

    for name, settings in collections.items():
        for action_name, user_ids in settings.get("collection", {}).items():
            # Remove 'Enabled' from the name
            short_name = action_name[:-7]
            key = f"{short_name}:{name}"
            if isinstance(user_ids, bool):
                actions.add(key)
            else:
                actions_by_user[key] = set(user_ids)

        for action_name, perms in settings.get("actions", {}).items():
            user_ids = perms["triggerEnabled"]
            key = f"custom:{action_name}:{name}"
            if isinstance(user_ids, bool):
                actions.add(key)
            else:
                actions_by_user[key] = set(user_ids)

    return actions, actions_by_user


def _decode_chart_permissions(stats: Dict[str, Any]):
    server_charts = list(itertools.chain(*stats.values()))
    hashes: List[str] = []
    for chart in server_charts:
        if isinstance(chart, str):  # Queries
            hashes.append(f"chart:{hash(chart)}")
        else:
            frontend_chart = {
                "type": chart.get("type"),
                "filters": chart.get("filter"),
                "aggregate": chart.get("aggregator"),
                "aggregate_field": chart.get("aggregateFieldName"),
                "collection": chart.get("sourceCollectionId"),
                "time_range": chart.get("timeRange"),
                "group_by_date_field": (chart.get("type") == "Line" and chart.get("groupByFieldName")) or None,
                "group_by_field": (chart.get("type") != "Line" and chart.get("groupByFieldName")) or None,
                "limit": chart.get("limit"),
                "label_field": chart.get("labelFieldName"),
                "relationship_field": chart.get("relationshipFieldName"),
            }
            h = hash(json.dumps(dict((k, v) for k, v in frontend_chart.items() if v is not None)))
            hashes.append(f"chart:{h}")
    return hashes


class PermissionServiceException(BaseException):
    def __init__(self, message: str, status: int = 403):
        self.STATUS = status
        self.message = message
        super(PermissionServiceException, self).__init__(message)


class PermissionService:
    def __init__(self, options: RoleOptions):
        self.options = options
        self.cache: TTLCache[int, Any] = TTLCache(maxsize=256, ttl=options["permission_cache_duration"])

    async def _get_rendering_permissions(self, rendering_id: int) -> PermissionBody:
        if rendering_id not in self.cache:
            permission_body = await ForestHttpApi.get_permissions(
                {
                    "env_secret": self.options["env_secret"],
                    "forest_server_url": self.options["forest_server_url"],
                    "is_production": self.options["is_production"],
                },
                rendering_id,
            )
            self.cache[rendering_id] = decode_permission_body(rendering_id, permission_body)
        return self.cache[rendering_id]

    def _invalidate_cache(self, rendering_id: int):
        if rendering_id in self.cache:
            del self.cache[rendering_id]

    async def _can(self, action: str, user: User, allowed_refetch: bool = True) -> Optional[Response]:
        perms = await self._get_rendering_permissions(user.rendering_id)
        is_allowed = action in perms["actions"] or user.user_id in perms["actions_by_user"].get(action, set())
        if not is_allowed and allowed_refetch:
            self._invalidate_cache(user.rendering_id)
            return await self._can(action, user, False)
        elif not is_allowed:
            raise PermissionServiceException("Unauthorized request")

    async def can(self, request: RequestCollection, action: str):
        if not request.user:
            raise PermissionServiceException("Unauthenticated request", 401)
        else:
            await self._can(action, request.user)

    async def get_scope(
        self,
        request: Union[RequestCollection, RequestRelationCollection],
        collection: Union[Collection, CustomizedCollection, None] = None,
    ) -> Optional[ConditionTree]:
        if not request.user:
            raise PermissionServiceException("Unauthenticated request", 401)
        else:
            perms = await self._get_rendering_permissions(request.user.rendering_id)
            name = request.collection.name
            if collection:
                name = collection.name
            try:
                scope: Scope = perms["scopes"][name]
            except KeyError:
                return None

            def build_scope_leaf(tree: ConditionTree) -> ConditionTree:
                if isinstance(tree, ConditionTreeLeaf):
                    dynamic_value = scope["dynamic_scope_values"].get(request.user.user_id)  # type: ignore
                    if isinstance(tree.value, str) and tree.value.startswith("$currentUser"):
                        if dynamic_value:
                            value = dynamic_value[tree.value]
                        elif tree.value.startswith("$currentUser.tags."):
                            value = request.user.tags[tree.value[18:]]  # type: ignore
                        else:
                            value = getattr(request.user, tree.value[13:])

                        return tree.override({"value": value})
                return tree

        return scope["condition_tree"].replace(build_scope_leaf)
