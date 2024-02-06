import asyncio
import os
import sys
from importlib.metadata import version
from typing import Literal, Optional, Tuple, Union

from flask import Blueprint, request
from flask.app import Flask
from flask.config import Config
from flask.wrappers import Request as FlaskRequest
from flask.wrappers import Response as FlaskResponse
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudLiteralMethod
from forestadmin.agent_toolkit.resources.security.resources import LiteralMethod as AuthLiteralMethod
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.flask_agent.exception import FlaskAgentException
from forestadmin.flask_agent.utils.dispatcher import get_dispatcher_method
from forestadmin.flask_agent.utils.requests import convert_request, convert_response


class FlaskAgent(BaseAgent):
    META: AgentMeta = {
        "liana": "agent-python",
        "liana_version": version("forestadmin-agent-flask").replace("b", "-beta."),
        # .replace because poetry force 0.0.1b25 instead of 0.0.1-beta.25
        # for more details:
        # https://python-poetry.org/docs/master/faq/ : "Why does Poetry not adhere to semantic versioning?"
        "stack": {"engine": "python", "engine_version": ".".join(map(str, [*sys.version_info[:3]]))},
    }

    def __init__(self, app: Flask):
        self.loop = asyncio.new_event_loop()
        self._app = app
        super(FlaskAgent, self).__init__(self.__parse_config(app.config))

        self._blueprint: Optional[Blueprint] = build_blueprint(self)
        if "csrf" in self._app.extensions:
            self._blueprint = self._app.extensions["csrf"].exempt(self._blueprint)
        self._app.register_blueprint(self.blueprint, url_prefix=f'{self.options["prefix"]}/forest')

    def __parse_config(self, flask_settings: Config) -> Options:
        settings: Options = {"schema_path": os.path.join(self._app.root_path, ".forestadmin-schema.json")}

        for key, value in flask_settings.items():
            if not key.upper().startswith("FOREST_"):
                continue

            forest_key = key.lower().replace("forest_", "")
            # Options.__annotations__ is a dict of {key_name:type_class}
            if forest_key not in Options.__annotations__.keys():
                ForestLogger.log("debug", f"Skipping unknown setting {key}.")
                continue

            value_type = Options.__annotations__[forest_key]
            try:
                settings[forest_key] = value_type(value)
            except Exception:
                settings[forest_key] = value

        if settings.get("is_production") is None:
            settings["is_production"] = not self._app.config["DEBUG"]

        return settings

    @property
    def blueprint(self) -> Blueprint:
        if not self._blueprint:
            raise FlaskAgentException("Flask agent must have the forest blueprint.")
        return self._blueprint

    def start(self):
        print("FLASK_RUN_FROM_CLI: ", os.environ.get("FLASK_RUN_FROM_CLI"))
        print("WERKZEUG_RUN_MAIN: ", os.environ.get("WERKZEUG_RUN_MAIN"))
        print("self._app.debug: ", self._app.debug)

        # if not os.environ.get("FLASK_RUN_FROM_CLI") == "true" or (  # run from wsgi process
        #     self._app.debug is not True and os.environ.get("WERKZEUG_RUN_MAIN") == "true"
        # ):
        self.loop.run_until_complete(self._start())
        ForestLogger.log("info", "Flask agent initialized")


def create_agent(app: Flask) -> FlaskAgent:
    with app.app_context():
        agent = FlaskAgent(app)
    return agent


def _after_request(response: FlaskResponse):
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


def build_blueprint(agent: FlaskAgent):  # noqa: C901
    blueprint = Blueprint("flask_forest", __name__)
    blueprint.after_request(_after_request)

    def _get_dispatch(
        request: FlaskRequest,
        method: Union[CrudLiteralMethod, AuthLiteralMethod, Literal["execute", "hook"], None] = None,
        detail: bool = False,
    ) -> Tuple[Request, Union[CrudLiteralMethod, AuthLiteralMethod, Literal["execute", "hook"]]]:
        if not method:
            meth = get_dispatcher_method(request.method, detail)
        else:
            meth = method
        return convert_request(request), meth

    async def _get_collection_response(
        request: FlaskRequest,
        resource: BaseResource,
        method: Optional[Union[AuthLiteralMethod, CrudLiteralMethod, Literal["execute", "hook"]]] = None,
        detail: bool = False,
    ) -> FlaskResponse:
        response = await resource.dispatch(*_get_dispatch(request, method=method, detail=detail))
        return convert_response(response)

    @blueprint.route("", methods=["GET"])
    async def index() -> FlaskResponse:  # type: ignore
        rsp = FlaskResponse()
        rsp.status = 200
        return rsp

    @blueprint.route("/authentication/callback", methods=["GET"])
    async def callback() -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["authentication"], "callback")

    @blueprint.route("/authentication", methods=["POST"])
    async def authentication() -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["authentication"], "authenticate")

    @blueprint.route("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/load", methods=["POST"])
    async def load_hook(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["actions"], "hook")

    @blueprint.route("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/change", methods=["POST"])
    async def change_hook(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["actions"], "hook")

    @blueprint.route("/_actions/<collection_name>/<int:action_name>/<slug>/hooks/search", methods=["POST"])
    async def search_hook(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["actions"], "hook")

    @blueprint.route("/_actions/<collection_name>/<int:action_name>/<slug>", methods=["POST"])
    async def actions(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["actions"], "execute")

    @blueprint.route("/stats/<collection_name>", methods=["POST"])
    async def stats(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["stats"])

    @blueprint.route("/_charts/<chart_name>", methods=["POST", "GET"])
    async def charts(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["datasource_charts"])

    @blueprint.route("/_charts/<collection_name>/<chart_name>", methods=["POST", "GET"])
    async def charts_collection(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["collection_charts"])

    @blueprint.route("/<collection_name>/count", methods=["GET"])
    async def count(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud"], "count")

    @blueprint.route("/<collection_name>/<pks>", methods=["GET", "PUT", "DELETE"])
    async def detail(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud"], detail=True)

    @blueprint.route("/<collection_name>", methods=["GET", "POST", "DELETE"])
    async def list_(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud"])

    @blueprint.route("/<collection_name>.csv", methods=["GET"])
    async def csv(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud"], "csv")

    @blueprint.route("/<collection_name>/<pks>/relationships/<relation_name>", methods=["GET", "POST", "DELETE", "PUT"])
    async def list_related(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud_related"])

    @blueprint.route("/<collection_name>/<pks>/relationships/<relation_name>/count", methods=["GET"])
    async def count_related(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud_related"], "count")

    @blueprint.route("/<collection_name>/<pks>/relationships/<relation_name>.csv", methods=["GET"])
    async def csv_related(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, (await agent.get_resources())["crud_related"], "csv")

    @blueprint.route("/scope-cache-invalidation", methods=["POST"])
    async def scope_cache_invalidation(**_) -> FlaskResponse:  # type: ignore
        agent._permission_service.invalidate_cache("forest.scopes")
        rsp = FlaskResponse(status=204)
        return rsp

    return blueprint
