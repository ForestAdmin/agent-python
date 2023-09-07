from typing import Dict

from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.agent_toolkit.utils.context_variables import ContextVariables


class ContextVariablesInstantiator:
    @staticmethod
    async def build_context_variables(
        caller: User, request_context_variables: Dict, permission: PermissionService
    ) -> ContextVariables:
        user = await permission.get_user_data(caller.user_id)
        team = await permission.get_team(caller.user_id)

        return ContextVariables(team, user, request_context_variables)
