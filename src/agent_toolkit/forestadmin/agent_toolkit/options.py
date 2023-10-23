import logging
from typing import Callable, Optional, TypedDict


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
    customize_error_message: Callable[[Exception], str]
    instant_cache_refresh: Optional[bool]
    skip_schema_update: Optional[bool]
    # typingsPath
    # typingsMaxDepth
    # skipSchemaUpdate
    # forestAdminClient


DEFAULT_OPTIONS: Options = {
    "is_production": False,
    "prefix": "",
    "forest_server_url": "https://api.forestadmin.com",
    "logger": None,
    "logger_level": logging.INFO,
    "customize_error_message": None,
    "permissions_cache_duration_in_seconds": 15 * 60,
    "instant_cache_refresh": None,
    "skip_schema_update": False,
}
