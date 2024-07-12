from typing import Any, Dict, Optional, Union

from cachetools import TTLCache
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.services.permissions.permissions_functions import (
    _decode_actions_permissions,
    _decode_crud_permissions,
    _decode_scope_permissions,
    _hash_chart,
)
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
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


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

    async def can_chart(self, request: RequestCollection) -> bool:
        hash_request = request.body["type"] + ":" + _hash_chart(request.body)
        is_allowed = hash_request in await self._get_chart_data(request.user.rendering_id, False)

        # Refetch
        if is_allowed is False:
            is_allowed = hash_request in await self._get_chart_data(request.user.rendering_id, True)

        # still not allowed - throw forbidden message
        if is_allowed is False:
            ForestLogger.log(
                "debug", f"User {request.user.user_id} cannot retrieve chart on rendering {request.user.rendering_id}"
            )
            raise ForbiddenError("You don't have permission to access this chart.")
        ForestLogger.log(
            "debug", f"User {request.user.user_id} can retrieve chart on rendering {request.user.rendering_id}"
        )
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
            ForestLogger.log("debug", "Fetching environment permissions")
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
        # TODO: avoid multiple computation of schema
        collections = await SchemaEmitter.generate(self.options["prefix"], collection.datasource)
        actions = [col for col in collections if col["name"] == collection.name][0]["actions"]
        if len(actions) == 0:
            return None

        actions = [
            action
            for action in actions
            if action["id"] == f"{collection.name}-{get_params['action_name']}-{get_params['slug']}"
        ]
        return actions[0] if len(actions) > 0 else None
