from forestadmin.agent_toolkit.exceptions import AgentToolkitException


class AuthenticationException(AgentToolkitException):
    STATUS = 401


class OpenIdException(AuthenticationException):
    def __init__(self, message: str, error: str, error_description: str, state: str) -> None:
        super().__init__(message)
        self.error = error
        self.error_description = error_description
        self.state = state
