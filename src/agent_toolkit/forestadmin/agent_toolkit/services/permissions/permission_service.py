import itertools
import json
import sys
from collections.abc import Iterable
from hashlib import sha1
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from cachetools import TTLCache
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestRelationCollection
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf


#########
# Type #
#########
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


##############
# Main class #
##############


class PermissionService:
    def __init__(self, options: RoleOptions):
        self.options = options
        self.cache: TTLCache[int, Any] = TTLCache(maxsize=256, ttl=options["permission_cache_duration"])

    async def can(self, caller: User, collection: Collection, action: str, allow_fetch: bool = False):
        if not await self._has_permission_system():
            return True

        user_data = await self.get_user_data(caller.user_id)
        collections_data = await self._get_collection_permissions_data(allow_fetch)

        is_allowed = (
            collection.name in collections_data and user_data["roleId"] in collections_data[collection.name][action]
        )

        # Refetch
        if is_allowed is False:
            collections_data = await self._get_collection_permissions_data(True)
            is_allowed = (
                collection.name in collections_data and user_data["roleId"] in collections_data[collection.name][action]
            )

        # still not allowed - throw forbidden message
        if is_allowed is False:
            raise ForbiddenError(f"You don't have permission to {action} this collection.")
        return is_allowed

    async def can_chart(self, caller: User, request: RequestCollection) -> bool:
        hash_request = request.body["type"] + ":" + _hash_chart(request.body)
        is_allowed = hash_request in await self._get_chart_data(request.user.rendering_id, False)

        # Refetch
        if is_allowed is False:
            is_allowed = hash_request in await self._get_chart_data(request.user.rendering_id, True)

        # still not allowed - throw forbidden message
        if is_allowed is False:
            ForestLogger.log(
                "debug", f"User {caller.user_id} cannot retrieve chart on rendering {request.user.rendering_id}"
            )
            raise ForbiddenError("You don't have permission to access this collection.")
        ForestLogger.log("debug", f"User {caller.user_id} can retrieve chart on rendering {request.user.rendering_id}")
        return is_allowed

    async def get_scope(
        self,
        request: Union[RequestCollection, RequestRelationCollection],
        collection: Union[Collection, CollectionCustomizer, None] = None,
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

    async def _has_permission_system(self) -> bool:
        if "forest.has_permission" not in self.cache:
            self.cache["forest.has_permission"] = not (await ForestHttpApi.get_environment_permissions(self.options))

        return self.cache["forest.has_permission"]

    async def get_user_data(self, user_id: int):
        if "forest.users" not in self.cache:
            users = {}
            ForestLogger.log("debug", "Refreshing user permissions cache")
            response = await ForestHttpApi.get_users(self.options)
            for user in response:
                users[user["id"]] = user
            self.cache["forest.users"] = users

        return self.cache["forest.users"][user_id]

    async def _get_chart_data(self, rendering_id: int, force_fetch: bool = False) -> Dict:
        if force_fetch and "forest.stats" in self.cache:
            del self.cache["forest.stats"]

        if "forest.stats" not in self.cache:
            ForestLogger.log("debug", f"Loading rendering permissions for rendering {rendering_id}")
            response = await ForestHttpApi.get_rendering_permissions(rendering_id, self.options)

            stat_hash = []
            for stat in response["stats"]:
                stat_hash.append(f'{stat["type"]}:{_hash_chart(stat)}')
            self.cache["forest.stats"] = stat_hash

        return self.cache["forest.stats"]

    async def _get_collection_permissions_data(self, force_fetch: bool = False):
        if force_fetch and "forest.collections" in self.cache:
            del self.cache["forest.collections"]

        if "forest.collections" not in self.cache:
            ForestLogger.log("Debug", "Fetching environment permissions")
            response = await ForestHttpApi.get_environment_permissions(self.options)
            collections = {}
            for name, collection in response.items():
                collections[name] = {
                    **_decode_crud_permissions(collection),
                    **_decode_actions_permissions(collection),
                }
        return self.cache["forest.collections"]


##################
# Decode methods #
##################


def _decode_crud_permissions(collection: Dict) -> Dict:
    return {
        "browse": collection["collection"]["browseEnabled"]["roles"],
        "read": collection["collection"]["readEnabled"]["roles"],
        "edit": collection["collection"]["editEnabled"]["roles"],
        "add": collection["collection"]["addEnabled"]["roles"],
        "delete": collection["collection"]["deleteEnabled"]["roles"],
        "export": collection["collection"]["exportEnabled"]["roles"],
    }


def _decode_actions_permissions(collection: Dict) -> Dict:
    actions = {"actions": {}}
    for id, action in collection["actions"].items():
        actions["actions"][id] = {
            "triggerEnabled": action["triggerEnabled"]["roles"],
            "triggerConditions": action["triggerConditions"],
            "approvalRequired": action["approvalRequired"]["roles"],
            "approvalRequiredConditions": action["approvalRequiredConditions"],
            "userApprovalEnabled": action["userApprovalEnabled"]["roles"],
            "userApprovalConditions": action["userApprovalConditions"],
            "selfApprovalEnabled": action["selfApprovalEnabled"]["roles"],
        }
    return actions


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


################
# Hash methods #
################


def _dict_hash(data: Dict) -> str:
    sorted_data = _order_dict(data)
    return sha1(json.dumps(sorted_data).encode()).hexdigest()


def _hash_chart(chart):
    known_chart_keys = [
        "type",
        "apiRoute",
        "smartRoute",
        "query",
        "labelFieldName",
        "filter",
        "sourceCollectionName",
        "aggregator",
        "aggregateFieldName",
        "groupByFieldName",
        "relationshipFieldName",
        "limit",
        "timeRange",
        "objective",
        "numeratorChartId",
        "denominatorChartId",
    ]
    dct = {
        k: v
        for k, v in chart.items()
        if k in known_chart_keys and v is not None and (not isinstance(v, Iterable) or len(v) > 0)
    }
    return _dict_hash(dct)


def _order_dict(dictionary):
    result = {}
    for key in sorted(dictionary.keys()):
        if isinstance(dictionary[key], dict):
            result[key] = _order_dict(dictionary[key])
        elif isinstance(dictionary[key], list):
            result[key] = []
            for i, _ in enumerate(dictionary[key]):
                result[key].append(_order_dict(dictionary[key][i]))
        else:
            result[key] = dictionary[key]
    return result
