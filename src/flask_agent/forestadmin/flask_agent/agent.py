import asyncio
from typing import Optional, Tuple, Union

from flask import Blueprint, request
from flask.wrappers import Request as FlaskRequest
from flask.wrappers import Response as FlaskResponse
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.options import AgentMeta, Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudLiteralMethod
from forestadmin.agent_toolkit.resources.security.resources import LiteralMethod as AuthLiteralMethod
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.flask_agent.utils.dispatcher import get_dispatcher_method
from forestadmin.flask_agent.utils.requests import convert_request, convert_response


class Agent(BaseAgent):

    META: AgentMeta = {
        "liana": "django-forestadmin",
        "liana_version": "1.3.1",
        "stack": {"database_type": "postgresql", "orm_version": "3.2.14"},
    }

    def __init__(self, options: Options):
        super(Agent, self).__init__(options)
        self._blueprint: Optional[Blueprint] = None
        self.loop = asyncio.get_event_loop()

    @property
    def blueprint(self) -> Blueprint:
        if not self._blueprint:
            raise
        return self._blueprint

    @blueprint.setter
    def blueprint(self, blueprint: Blueprint):
        self._blueprint = blueprint


def build_agent(options: Options) -> Agent:
    agent = Agent(options)
    agent.blueprint = build_blueprint(agent)
    return agent


def _after_request(response: FlaskResponse):
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


def build_blueprint(agent: Agent):
    blueprint = Blueprint("flask_forest", __name__)
    blueprint.after_request(_after_request)
    crud_resource = agent.resources["crud"]
    crud_related_resource = agent.resources["crud_related"]
    auth_resource = agent.resources["authentication"]

    def _get_dispatch(
        request: FlaskRequest, method: Optional[AuthLiteralMethod] = None, detail: bool = False
    ) -> Tuple[Request, Union[CrudLiteralMethod, AuthLiteralMethod]]:
        if not method:
            meth = get_dispatcher_method(request.method, detail)
        else:
            meth = method
        return convert_request(request), meth

    async def _get_collection_response(
        request: FlaskRequest,
        resource: BaseResource,
        method: Optional[Union[AuthLiteralMethod, CrudLiteralMethod]] = None,
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
        return await _get_collection_response(request, auth_resource, "callback")

    @blueprint.route("/authentication", methods=["POST"])
    async def authentication() -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, auth_resource, "authenticate")

    @blueprint.route("/<collection_name>/count", methods=["GET"])
    async def count(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, crud_resource, "count")

    @blueprint.route("/<collection_name>/<pks>", methods=["GET", "PUT", "DELETE"])
    async def detail(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, crud_resource, detail=True)

    @blueprint.route("/<collection_name>", methods=["GET", "POST", "DELETE"])
    async def list(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, crud_resource)

    @blueprint.route("/<collection_name>/<pks>/relationships/<relation_name>", methods=["GET", "POST", "DELETE", "PUT"])
    async def list_related(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, crud_related_resource)

    @blueprint.route("/<collection_name>/<pks>/relationships/<relation_name>/count", methods=["GET"])
    async def count_related(**_) -> FlaskResponse:  # type: ignore
        return await _get_collection_response(request, crud_related_resource, "count")

    return blueprint
