import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class Options(TypedDict):
    # application_url: str  # useless for now
    auth_secret: str
    prefix: str
    env_secret: str
    forest_server_url: str
    is_production: bool
    schema_path: str
    # logger
    # loggerLevel
    # typingsPath
    # typingsMaxDepth
    # permissionsCacheDurationInSeconds
    # skipSchemaUpdate
    # forestAdminClient


DEFAULT_OPTIONS: Options = {
    "is_production": False,
    "prefix": "forest",
    "forest_server_url": "https://api.forestadmin.com",
}
