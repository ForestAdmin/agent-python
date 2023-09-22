import logging
import os
from distutils.util import strtobool

from demo.forest_admin.forest_logging_customization import custom_error_message_fn, custom_logger_fn
from forestadmin.agent_toolkit.options import Options

SETTINGS: Options = {
    "env_secret": os.environ.get("FOREST_ENV_SECRET"),
    "auth_secret": os.environ.get("FOREST_AUTH_SECRET"),
    "forest_server_url": os.environ.get("FOREST_SERVER_URL", "https://api.forestadmin.com"),
    "is_production": strtobool(os.environ.get("FOREST_IS_PRODUCTION")),
    "instant_cache_refresh": os.environ.get("INSTANT_CACHE_REFRESH", False),
    "logger_level": logging.DEBUG,
    "logger": lambda level, message: custom_logger_fn(level, message),
    "customize_error_message": custom_error_message_fn,
}
