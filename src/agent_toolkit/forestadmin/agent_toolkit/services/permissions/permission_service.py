import itertools
import json
import sys
from collections.abc import Iterable
from hashlib import sha1
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from cachetools import TTLCache
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.services.permissions.smart_actions_checker import SmartActionChecker
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.agent_toolkit.utils.context_variable_injector import ContextVariableInjector
from forestadmin.agent_toolkit.utils.context_variables import ContextVariables
from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerAction
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.exceptions import ForbiddenError, ForestException
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


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

    def invalidate_cache(self, key: str):
        if key in self.cache:
            del self.cache[key]

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

    async def can_smart_action(
        self, request: RequestCollection, collection: Collection, filter_: Filter, allow_fetch: bool = True
    ):
        if not await self._has_permission_system():
            return True

        user_data = await self.get_user_data(request.user.user_id)
        collection_data = await self._get_collection_permissions_data(allow_fetch)
        action = await self._find_action_from_endpoint(collection, request.query, request.method)

        if action is None:
            raise ForestException(f"The collection {collection.name} does not have this smart action")

        smart_action_approval = SmartActionChecker(
            request,
            collection,
            collection_data[collection.name]["actions"][action["name"]],
            request.user,
            user_data["roleId"],
            filter_,
        )
        # can_execute raise error if unauthorized
        is_allowed = await smart_action_approval.can_execute()

        allowed_txt = "not allowed" if not is_allowed else "allowed"
        ForestLogger.log("debug", f"User {user_data['roleId']} is {allowed_txt} to perform {action['name']}")

        return is_allowed

    async def get_scope(
        self,
        caller: User,
        collection: Union[Collection, CollectionCustomizer],
    ) -> Optional[ConditionTree]:
        permissions = await self._get_scope_and_team_data(caller.rendering_id)
        scope = permissions["scopes"].get(collection.name)
        if scope is None:
            return None

        team = permissions["team"]
        user = await self.get_user_data(caller.user_id)

        context_variable = ContextVariables(team, user)
        return ContextVariableInjector.inject_context_in_filter(scope, context_variable)

    async def _has_permission_system(self) -> bool:
        if "forest.has_permission" not in self.cache:
            self.cache["forest.has_permission"] = not (
                await ForestHttpApi.get_environment_permissions(self.options) is True
            )

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

    async def get_team(self, rendering_id: int):
        permissions = await self._get_scope_and_team_data(rendering_id)
        return permissions["team"]

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
            for name, collection in response["collections"].items():
                collections[name] = {
                    **_decode_crud_permissions(collection),
                    **_decode_actions_permissions(collection),
                }
            self.cache["forest.collections"] = collections

        return self.cache["forest.collections"]

    async def _get_scope_and_team_data(self, rendering_id: int):
        if "forest.scopes" not in self.cache:
            response = await ForestHttpApi.get_rendering_permissions(rendering_id, self.options)
            data = {"scopes": _decode_scope_permissions(response["collections"]), "team": response["team"]}

            self.cache["forest.scopes"] = data

        return self.cache["forest.scopes"]

    async def _find_action_from_endpoint(
        self, collection: Collection, get_params: Dict, http_method: str
    ) -> Optional[ForestServerAction]:
        actions = await SchemaEmitter.generate(self.options["prefix"], collection.datasource)
        actions = [col for col in actions if col["name"] == collection.name][0]["actions"]
        if len(actions) == 0:
            return None

        actions = [
            action
            for action in actions
            if action["id"] == f"{collection.name}-{get_params['action_name']}-{get_params['slug']}"
            and http_method.value == action["httpMethod"]
        ]
        return actions[0]


##################
# Decode methods #
##################


def _decode_scope_permissions(raw_permission: Dict):
    scopes = {}
    for collection_name, value in raw_permission.items():
        if value.get("scope") is not None:
            scopes[collection_name] = ConditionTreeFactory.from_plain_object(value["scope"])
    return scopes


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
