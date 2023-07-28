import logging
import sys
from typing import Callable

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
    logger: Callable[[str, str], None]
    logger_level: int
    permissions_cache_duration_in_seconds: int
    # typingsPath
    # typingsMaxDepth
    # permissionsCacheDurationInSeconds
    # skipSchemaUpdate
    # forestAdminClient


DEFAULT_OPTIONS: Options = {
    "is_production": False,
    "prefix": "forest",
    "forest_server_url": "https://api.forestadmin.com",
    "logger": None,
    "logger_level": logging.DEBUG,
    "permissions_cache_duration_in_seconds": 15 * 60,
}
