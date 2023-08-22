from typing import Dict, Optional


class ContextVariables:
    USER_VALUE_PREFIX: str = "currentUser."
    USER_VALUE_TAG_PREFIX: str = "currentUser.tags."
    USER_VALUE_TEAM_PREFIX: str = "currentUser.team."

    def __init__(self, team: Dict, user: Dict, request_context_variables: Optional[Dict] = None):
        self.team = team
        self.user = user
        self.request_context_variables = request_context_variables

    def get_value(self, context_variable_key: str):
        if context_variable_key.startswith(ContextVariables.USER_VALUE_PREFIX):
            return self._get_current_user_data(context_variable_key)

        return self.request_context_variables[context_variable_key]

    def _get_current_user_data(self, context_variable_key: str):
        if context_variable_key.startswith(ContextVariables.USER_VALUE_TEAM_PREFIX):
            return self.team[context_variable_key[len(ContextVariables.USER_VALUE_TEAM_PREFIX) :]]

        if context_variable_key.startswith(ContextVariables.USER_VALUE_TAG_PREFIX):
            return self.user["tags"][context_variable_key[len(ContextVariables.USER_VALUE_TAG_PREFIX) :]]

        return self.user[context_variable_key[len(ContextVariables.USER_VALUE_PREFIX) :]]
