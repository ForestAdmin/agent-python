from typing import TypedDict


class RoleOptions(TypedDict):
    server_url: str
    env_secret: str
    is_production: bool
    permission_cache_duration: int
    prefix: str
