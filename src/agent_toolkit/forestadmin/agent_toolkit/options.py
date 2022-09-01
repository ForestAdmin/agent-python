from typing import TypedDict


class Options(TypedDict):
    application_url: str
    agent_url: str
    auth_secret: str
    prefix: str
    env_secret: str
    forest_server_url: str
    is_production: bool
