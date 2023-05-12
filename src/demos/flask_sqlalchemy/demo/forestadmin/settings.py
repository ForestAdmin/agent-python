import os
from distutils.util import strtobool

from forestadmin.agent_toolkit.options import Options

SETTINGS: Options = {
    "env_secret": os.environ.get("FOREST_ENV_SECRET"),
    "auth_secret": os.environ.get("FOREST_AUTH_SECRET"),
    "server_url": os.environ.get("FOREST_SERVER_URL"),
    "is_production": strtobool(os.environ.get("FOREST_IS_PRODUCTION")),
}
