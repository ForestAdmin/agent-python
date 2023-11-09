import asyncio
import os
import sys

import pkg_resources
from django.conf import settings
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta


class DjangoAgent(BaseAgent):
    META: AgentMeta = {
        "liana": "agent-python",
        "liana_version": pkg_resources.get_distribution("forestadmin-agent-django").version.replace("b", "-beta."),
        # .replace because poetry force 0.0.1b25 instead of 0.0.1-beta.25
        # for more details:
        # https://python-poetry.org/docs/master/faq/ : "Why does Poetry not adhere to semantic versioning?"
        "stack": {"engine": "python", "engine_version": ".".join(map(str, [*sys.version_info[:3]]))},
    }

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        super(DjangoAgent, self).__init__(self.__parse_config())

    def __parse_config(self):
        options: Options = {"schema_path": os.path.join(settings.BASE_DIR, ".forestadmin-schema.json")}
        for setting_name in dir(settings):
            if not setting_name.upper().startswith("FOREST_"):
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
