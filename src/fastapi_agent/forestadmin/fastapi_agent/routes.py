from fastapi import APIRouter, Request
from forestadmin.agent_toolkit.agent import Resources
from forestadmin.agent_toolkit.resources.actions.resources import ActionResource
from forestadmin.agent_toolkit.resources.actions.resources import LiteralMethod as ActionLiteralMethod
from forestadmin.agent_toolkit.resources.collections.crud import CrudResource
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudLiteralMethod
from forestadmin.agent_toolkit.resources.collections.crud_related import CrudRelatedResource
from forestadmin.agent_toolkit.resources.collections.crud_related import LiteralMethod as CrudRelatedLiteralMethod
from forestadmin.agent_toolkit.resources.security.resources import Authentication
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.fastapi_agent.utils.requests import convert_request, convert_response


def make_router(prefix: str, resources: Resources, permission_service: PermissionService) -> APIRouter:
    router = APIRouter(prefix=f"{prefix}/forest")

    @router.get("", status_code=204)
    async def forest():
        pass

    @router.post("/scope-cache-invalidation", status_code=204)
    async def scope_cache_invalidation():
        permission_service.invalidate_cache("forest.scopes")

    @router.post("/stats/{collection_name}")
    async def stats(request: Request):
        resource = resources["stats"]
        ret = await resource.dispatch(await convert_request(request))
        return convert_response(ret)

    @router.post("/_charts/{collection_name}/{chart_name}")
    @router.get("/_charts/{collection_name}/{chart_name}")
    async def charts_collection(request: Request):
        resource = resources["collection_charts"]
        ret = await resource.dispatch(await convert_request(request))
        return convert_response(ret)

    @router.post("/_charts/{chart_name}")
    @router.get("/_charts/{chart_name}")
    async def charts_datasource(request: Request):
        resource = resources["datasource_charts"]
        ret = await resource.dispatch(await convert_request(request))
        return convert_response(ret)

    router.include_router(_build_authentication_router(resources["authentication"]))
    router.include_router(_build_crud_router(resources["crud"]))
    router.include_router(_build_crud_related_router(resources["crud_related"]))
    router.include_router(_build_action_router(resources["actions"]))
    return router


def _build_authentication_router(resource: Authentication) -> APIRouter:
    router = APIRouter(prefix="/authentication")

    @router.post("")
    async def authentication(request: Request):
        ret = await resource.dispatch(await convert_request(request), "authenticate")
        return convert_response(ret)

    @router.get("/callback")
    async def callback(request: Request):
        ret = await resource.dispatch(await convert_request(request), "callback")
        return convert_response(ret)

    return router


def _build_crud_router(resource: CrudResource) -> APIRouter:
    router = APIRouter()

    async def collection_crud_resource(request: Request, verb: CrudLiteralMethod):
        ret = await resource.dispatch(await convert_request(request), verb)
        return convert_response(ret)

    # list
    @router.get("/{collection_name}.csv")
    async def collection_csv(request: Request):
        return await collection_crud_resource(request, "csv")

    @router.get("/{collection_name}")
    async def collection_list_get(request: Request):
        return await collection_crud_resource(request, "list")

    @router.post("/{collection_name}")
    async def collection_list_post(request: Request):
        return await collection_crud_resource(request, "add")

    @router.delete("/{collection_name}")
    async def collection_list_delete(request: Request):
        return await collection_crud_resource(request, "delete_list")

    @router.get("/{collection_name}/count")
    async def collection_count(request: Request):
        return await collection_crud_resource(request, "count")

    # detail
    @router.put("/{collection_name}/{pks}")
    async def collection_detail_put(request: Request):
        return await collection_crud_resource(request, "update")

    @router.get("/{collection_name}/{pks}")
    async def collection_detail_get(request: Request):
        return await collection_crud_resource(request, "get")

    @router.delete("/{collection_name}/{pks}")
    async def collection_detail_del(request: Request):
        return await collection_crud_resource(request, "delete")

    return router


def _build_crud_related_router(resource: CrudRelatedResource) -> APIRouter:
    router = APIRouter()

    async def collection_crud_related_resource(request: Request, verb: CrudRelatedLiteralMethod):
        ret = await resource.dispatch(await convert_request(request), verb)
        return convert_response(ret)

    @router.get("/{collection_name}/{pks}/relationships/{relation_name}.csv")
    async def collection_related_csv_get(request: Request):
        return await collection_crud_related_resource(request, "csv")

    @router.get("/{collection_name}/{pks}/relationships/{relation_name}")
    async def collection_related_list_get(request: Request):
        return await collection_crud_related_resource(request, "list")

    @router.post("/{collection_name}/{pks}/relationships/{relation_name}")
    async def collection_related_list_post(request: Request):
        return await collection_crud_related_resource(request, "add")

    @router.delete("/{collection_name}/{pks}/relationships/{relation_name}")
    async def collection_related_list_delete(request: Request):
        return await collection_crud_related_resource(request, "delete_list")

    @router.put("/{collection_name}/{pks}/relationships/{relation_name}")
    async def collection_related_list_put(request: Request):
        return await collection_crud_related_resource(request, "update_list")

    @router.get("/{collection_name}/{pks}/relationships/{relation_name}/count")
    async def collection_related_count_get(request: Request):
        return await collection_crud_related_resource(request, "count")

    return router


def _build_action_router(resource: ActionResource) -> APIRouter:
    router = APIRouter(prefix="/_actions/{collection_name}/{action_name:int}/{slug}")

    async def action_resource(request: Request, verb: ActionLiteralMethod):
        ret = await resource.dispatch(await convert_request(request), verb)
        return convert_response(ret)

    @router.post("")
    async def execute(request: Request):
        return await action_resource(request, "execute")

    @router.post("/hooks/load")
    async def hook_load(request: Request):
        return await action_resource(request, "hook")

    @router.post("/hooks/change")
    async def hook_change(request: Request):
        return await action_resource(request, "hook")

    @router.post("/hooks/search")
    async def hook_search(request: Request):
        return await action_resource(request, "hook")

    return router
