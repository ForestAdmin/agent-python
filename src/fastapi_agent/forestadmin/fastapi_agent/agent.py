import sys
from importlib.metadata import version

from fastapi import APIRouter, FastAPI
from fastapi import Request as FastAPIRequest
from forestadmin.agent_toolkit.agent import Agent as BaseAgent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.actions.resources import LiteralMethod as ActionLiteralMethod
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudLiteralMethod
from forestadmin.agent_toolkit.resources.collections.crud_related import LiteralMethod as CrudRelatedLiteralMethod
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.fastapi_agent.utils.requests import convert_request, convert_response


class FastAPIAgent(BaseAgent):
    META: AgentMeta = {
        "liana": "agent-python",
        "liana_version": version("forestadmin-agent-fastapi").replace("b", "-beta."),
        # .replace because poetry force 0.0.1b25 instead of 0.0.1-beta.25
        # for more details:
        # https://python-poetry.org/docs/master/faq/ : "Why does Poetry not adhere to semantic versioning?"
        "stack": {"engine": "python", "engine_version": ".".join(map(str, [*sys.version_info[:3]]))},
    }

    def __init__(self, app: FastAPI, settings: Options):
        self._app: FastAPI = app
        self._settings: Options = settings
        self._app.add_event_handler("startup", self.start)
        self._mount_router()

        super().__init__(self.__parse_config(settings))

        # TODO: check for:
        # * csrf
        # self._blueprint: Optional[Blueprint] = build_blueprint(self)
        # if "csrf" in self._app.extensions:
        #     self._blueprint = self._app.extensions["csrf"].exempt(self._blueprint)
        # self._app.register_blueprint(self.blueprint, url_prefix=f'{self.options["prefix"]}/forest')

    def __parse_config(self, fastapi_settings: Options) -> Options:
        # TODO: file a way to get ROOT_PATH
        settings: Options = {"schema_path": "./.forestadmin-schema.json"}  # type:ignore

        for key, value in fastapi_settings.items():
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
            settings["is_production"] = not self._app.debug

        return settings

    def _mount_router(self):
        router = APIRouter(prefix="/forest")  # TODO: option["prefix"]

        @router.get("", status_code=204)
        async def forest():
            pass

        @router.post("/scope-cache-invalidation", status_code=204)
        async def scope_cache_invalidation():
            self._permission_service.invalidate_cache("forest.scopes")

        @router.post("/stats/{collection_name}")
        async def stats(request: FastAPIRequest):
            resource = (await self.get_resources())["stats"]
            ret = await resource.dispatch(await convert_request(request))
            return convert_response(ret)

        @router.post("/_charts/{collection_name}/{chart_name}")
        @router.get("/_charts/{collection_name}/{chart_name}")
        async def charts_collection(request: FastAPIRequest):
            resource = (await self.get_resources())["collection_charts"]
            ret = await resource.dispatch(await convert_request(request))
            return convert_response(ret)

        @router.post("/_charts/{chart_name}")
        @router.get("/_charts/{chart_name}")
        async def charts_datasource(request: FastAPIRequest):
            resource = (await self.get_resources())["datasource_charts"]
            ret = await resource.dispatch(await convert_request(request))
            return convert_response(ret)

        router.include_router(self._build_authentication_router())
        router.include_router(self._build_crud_router())
        router.include_router(self._build_crud_related_router())
        router.include_router(self._build_action_router())

        self._app.include_router(router)
        self._router = router

    def _build_authentication_router(self) -> APIRouter:
        router = APIRouter(prefix="/authentication")

        @router.post("")
        async def authentication(request: FastAPIRequest):
            resource = (await self.get_resources())["authentication"]
            ret = await resource.dispatch(await convert_request(request), "authenticate")
            return convert_response(ret)

        @router.get("/callback")
        async def callback(request: FastAPIRequest):
            resource = (await self.get_resources())["authentication"]
            ret = await resource.dispatch(await convert_request(request), "callback")
            return convert_response(ret)

        return router

    def _build_crud_router(self) -> APIRouter:
        router = APIRouter()

        async def collection_crud_resource(request: FastAPIRequest, verb: CrudLiteralMethod):
            resource = (await self.get_resources())["crud"]
            ret = await resource.dispatch(await convert_request(request), verb)
            return convert_response(ret)

        # list
        @router.get("/{collection_name}.csv")
        async def collection_csv(request: FastAPIRequest):
            return await collection_crud_resource(request, "csv")

        @router.get("/{collection_name}")
        async def collection_list_get(request: FastAPIRequest):
            return await collection_crud_resource(request, "list")

        @router.post("/{collection_name}")
        async def collection_list_post(request: FastAPIRequest):
            return await collection_crud_resource(request, "add")

        @router.delete("/{collection_name}")
        async def collection_list_delete(request: FastAPIRequest):
            return await collection_crud_resource(request, "delete_list")

        @router.get("/{collection_name}/count")
        async def collection_count(request: FastAPIRequest):
            return await collection_crud_resource(request, "count")

        # detail
        @router.put("/{collection_name}/{pks}")
        async def collection_detail_put(request: FastAPIRequest):
            return await collection_crud_resource(request, "update")

        @router.get("/{collection_name}/{pks}")
        async def collection_detail_get(request: FastAPIRequest):
            return await collection_crud_resource(request, "get")

        @router.delete("/{collection_name}/{pks}")
        async def collection_detail_del(request: FastAPIRequest):
            return await collection_crud_resource(request, "delete")

        return router

    def _build_crud_related_router(self) -> APIRouter:
        router = APIRouter()

        async def collection_crud_related_resource(request: FastAPIRequest, verb: CrudRelatedLiteralMethod):
            resource = (await self.get_resources())["crud_related"]
            ret = await resource.dispatch(await convert_request(request), verb)
            return convert_response(ret)

        @router.get("/{collection_name}/{pks}/relationships/{relation_name}.csv")
        async def collection_related_csv_get(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "csv")

        @router.get("/{collection_name}/{pks}/relationships/{relation_name}")
        async def collection_related_list_get(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "list")

        @router.post("/{collection_name}/{pks}/relationships/{relation_name}")
        async def collection_related_list_post(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "add")

        @router.delete("/{collection_name}/{pks}/relationships/{relation_name}")
        async def collection_related_list_delete(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "delete_list")

        @router.put("/{collection_name}/{pks}/relationships/{relation_name}")
        async def collection_related_list_put(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "update_list")

        @router.get("/{collection_name}/{pks}/relationships/{relation_name}/count")
        async def collection_related_count_get(request: FastAPIRequest):
            return await collection_crud_related_resource(request, "count")

        return router

    def _build_action_router(self) -> APIRouter:
        router = APIRouter(prefix="/_actions/{collection_name}/{action_name:int}/{slug}")

        async def action_resource(request: FastAPIRequest, verb: ActionLiteralMethod):
            resource = (await self.get_resources())["actions"]
            ret = await resource.dispatch(await convert_request(request), verb)
            return convert_response(ret)

        @router.post("")
        async def execute(request: FastAPIRequest):
            return await action_resource(request, "execute")

        @router.post("/hooks/load")
        async def hook_load(request: FastAPIRequest):
            return await action_resource(request, "hook")

        @router.post("/hooks/change")
        async def hook_change(request: FastAPIRequest):
            return await action_resource(request, "hook")

        @router.post("/hooks/search")
        async def hook_search(request: FastAPIRequest):
            return await action_resource(request, "hook")

        return router

    async def start(self):
        await self._start()
        ForestLogger.log("info", "FastAPI agent initialized")


def create_agent(app: FastAPI, settings) -> FastAPIAgent:
    agent = FastAPIAgent(app, settings)
    return agent


# def _after_request(response: FlaskResponse):
#     response.headers["Access-Control-Allow-Private-Network"] = "true"
#     return response
