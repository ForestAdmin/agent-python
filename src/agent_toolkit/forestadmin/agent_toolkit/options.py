import sys

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from typing_extensions import Literal, TypedDict


class AgentStackMeta(TypedDict, total=False):
    engine: Literal["python"]
    engine_version: str
    database_type: str
    orm_version: str


class AgentMeta(TypedDict):
    liana: str
    liana_version: str
    stack: AgentStackMeta


class Options(TypedDict):
    application_url: str
    agent_url: str
    auth_secret: str
    prefix: str
    env_secret: str
    forest_server_url: str
    is_production: bool
