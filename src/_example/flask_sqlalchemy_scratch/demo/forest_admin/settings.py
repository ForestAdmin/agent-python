import os
from distutils.util import strtobool

from forestadmin.agent_toolkit.options import Options

SETTINGS: Options = {
    "env_secret": os.environ.get("FOREST_ENV_SECRET"),
    "auth_secret": os.environ.get("FOREST_AUTH_SECRET"),
    "forest_server_url": os.environ.get("FOREST_SERVER_URL", "https://api.forestadmin.com"),
    "is_production": strtobool(os.environ.get("FOREST_IS_PRODUCTION")),
}
