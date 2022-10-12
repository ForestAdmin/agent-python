from forestadmin.agent_toolkit.exceptions import AgentToolkitException


class AuthenticationException(AgentToolkitException):
    STATUS = 401
