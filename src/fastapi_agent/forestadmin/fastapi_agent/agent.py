import sys
from importlib.metadata import version

from fastapi import FastAPI
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.fastapi_agent.routes import make_router
from forestadmin.fastapi_agent.settings import ForestFastAPISettings


class FastAPIAgent(BaseAgent):
    META: AgentMeta = {
        "liana": "agent-python",
        "liana_version": version("forestadmin-agent-fastapi").replace("b", "-beta."),
        # .replace because poetry force 0.0.1b25 instead of 0.0.1-beta.25
        # for more details:
        # https://python-poetry.org/docs/master/faq/ : "Why does Poetry not adhere to semantic versioning?"
        "stack": {"engine": "python", "engine_version": ".".join(map(str, [*sys.version_info[:3]]))},
    }

    def __init__(self, app: FastAPI, settings: ForestFastAPISettings):
        self._app: FastAPI = app
        self._app.add_event_handler("startup", self.start)
        super().__init__(self.__parse_config(settings))

    def __parse_config(self, fast_api_settings: ForestFastAPISettings) -> Options:
        # it's not possible to get root path of a fastapi project, so let's the user fill this setting
        settings: Options = {}  # type:ignore

        for key, value in fast_api_settings.model_dump().items():
            if key not in Options.__annotations__.keys():
                ForestLogger.log("warning", f"Skipping unknown setting {key}.")
                continue

            value_type = Options.__annotations__[key]
            try:
                settings[key] = value_type(value)
            except Exception:
                settings[key] = value

        if settings.get("is_production") is None:
            settings["is_production"] = not self._app.debug

        return settings

    async def _mount_router(self):
        router = make_router(self.options["prefix"], await self.get_resources(), self._permission_service)
        self._app.include_router(router)
        self._router = router

    async def start(self):
        await self._mount_router()
        await self._start()
        ForestLogger.log("info", "FastAPI agent initialized")


def create_agent(app: FastAPI, settings: ForestFastAPISettings) -> FastAPIAgent:
    agent = FastAPIAgent(app, settings)
    return agent
