import asyncio
import importlib
import os
import sys
from importlib.metadata import version
from typing import Optional

from django.conf import ENVIRONMENT_VARIABLE as DJANGO_SETTING_MODULE_ENV_VAR_NAME
from django.conf import settings
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta


class DjangoAgent(BaseAgent):
    META: AgentMeta = {
        "liana": "agent-python",
        "liana_version": version("forestadmin-agent-django").replace("b", "-beta."),
        # .replace because poetry force 0.0.1b25 instead of 0.0.1-beta.25
        # for more details:
        # https://python-poetry.org/docs/master/faq/ : "Why does Poetry not adhere to semantic versioning?"
        "stack": {"engine": "python", "engine_version": ".".join(map(str, [*sys.version_info[:3]]))},
    }

    def __init__(self, config: Optional[Options] = None):
        self.loop = asyncio.new_event_loop()
        config = config if config is not None else self.__parse_config()
        super(DjangoAgent, self).__init__(config)

    def __parse_config(self) -> Options:
        django_only_settings = ["FOREST_CUSTOMIZE_FUNCTION"]
        if getattr(settings, "BASE_DIR", None) is not None:
            base_dir = settings.BASE_DIR
        else:
            setting_file = importlib.import_module(os.environ[DJANGO_SETTING_MODULE_ENV_VAR_NAME]).__file__
            base_dir = os.path.abspath(os.path.join(setting_file, "..", ".."))

        options: Options = {"schema_path": os.path.join(base_dir, ".forestadmin-schema.json")}
        for setting_name in dir(settings):
            if not setting_name.upper().startswith("FOREST_"):
                continue

            if setting_name in django_only_settings:
                continue

            forest_key = setting_name.lower().replace("forest_", "")
            # Options.__annotations__ is a dict of {key_name:type_class}
            if forest_key not in Options.__annotations__.keys():
                ForestLogger.log("debug", f"Skipping unknown setting {setting_name}.")
                continue

            setting_value = getattr(settings, setting_name)

            value_type = Options.__annotations__[forest_key]
            try:
                options[forest_key] = value_type(setting_value)
            except Exception:
                options[forest_key] = setting_value

        if options.get("is_production") is None:
            options["is_production"] = not settings.DEBUG
        return options

    def start(self):
        self.loop.run_until_complete(self._start())
        ForestLogger.log("info", "Django agent initialized")


def create_agent(config: Optional[Options] = None):
    agent = DjangoAgent(config)
    return agent
