from forestadmin.agent_toolkit.exceptions import AgentToolkitException


class JsonApiException(AgentToolkitException):
    pass


class JsonApiSerializerException(JsonApiException):
    pass


class JsonApiDeserializerException(JsonApiException):
    pass
