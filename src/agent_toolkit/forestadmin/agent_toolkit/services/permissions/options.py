import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class RoleOptions(TypedDict):
    forest_server_url: str
    env_secret: str
    is_production: bool
    permission_cache_duration: int
