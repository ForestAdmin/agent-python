import logging
import os

from demo.forest_admin.forest_logging_customization import custom_error_message_fn, custom_logger_fn
from dotenv import load_dotenv

load_dotenv()  # load .env file into environ variables


class FlaskConfig(object):
    FOREST_ENV_SECRET = os.environ.get("FOREST_ENV_SECRET")
    FOREST_AUTH_SECRET = os.environ.get("FOREST_AUTH_SECRET")
    FOREST_SERVER_URL = os.environ.get("FOREST_SERVER_URL", "https://api.forestadmin.com")
    FOREST_IS_PRODUCTION = os.environ.get("FOREST_IS_PRODUCTION", False)
    FOREST_LOGGER_LEVEL = logging.DEBUG
    # FOREST_LOGGER = lambda level, message: custom_logger_fn(level, message),
    FOREST_LOGGER = custom_logger_fn
    FOREST_CUSTOMIZE_ERROR_MESSAGE = custom_error_message_fn
