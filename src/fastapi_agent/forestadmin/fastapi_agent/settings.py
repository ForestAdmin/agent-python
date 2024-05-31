from typing import Callable, Optional

from forestadmin.agent_toolkit.options import OptionValidator
from pydantic import BaseModel


class ForestFastAPISettings(BaseModel):
    auth_secret: str
    env_secret: str
    schema_path: str

    prefix: Optional[str] = OptionValidator.DEFAULT_OPTIONS["prefix"]
    server_url: Optional[str] = OptionValidator.DEFAULT_OPTIONS["server_url"]
    is_production: Optional[bool] = None  # will be 'not app.debug'

    logger: Optional[Callable[[str, str], None]] = OptionValidator.DEFAULT_OPTIONS["logger"]
    logger_level: Optional[int] = OptionValidator.DEFAULT_OPTIONS["logger_level"]
    customize_error_message: Optional[Callable[[Exception], str]] = OptionValidator.DEFAULT_OPTIONS[
        "customize_error_message"
    ]

    permissions_cache_duration_in_seconds: Optional[int] = OptionValidator.DEFAULT_OPTIONS[
        "permissions_cache_duration_in_seconds"
    ]
    instant_cache_refresh: Optional[bool] = None  # will be True if is_production is True

    skip_schema_update: Optional[bool] = OptionValidator.DEFAULT_OPTIONS["skip_schema_update"]
    verify_ssl: Optional[bool] = OptionValidator.DEFAULT_OPTIONS["verify_ssl"]
