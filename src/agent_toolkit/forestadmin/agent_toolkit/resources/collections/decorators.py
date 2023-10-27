from typing import Any, Awaitable, Callable, TypeVar, Union

from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.filter import parse_timezone
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.utils.context import (
    FileResponse,
    HttpResponseBuilder,
    Request,
    RequestMethod,
    Response,
    User,
)
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from jose import JWTError, jwt

BoundRequest = TypeVar("BoundRequest", bound=Request)
BoundResource = TypeVar("BoundResource", bound=BaseCollectionResource)
BoundRequestCollection = TypeVar("BoundRequestCollection", bound=RequestCollection)


async def _authenticate(
    self: "BoundResource",
    request: BoundRequestCollection,
    decorated_fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]],
):
    if not request.headers:
        return Response(status=401)

    try:
        authorization = request.headers["Authorization"]
    except KeyError:
        return Response(status=401)

    try:
        token = authorization.split("Bearer ")[1]
    except IndexError:
        return Response(status=401)

    try:
        user = jwt.decode(token, self.option["auth_secret"])
    except JWTError:
        return Response(status=401)

    request.user = User(
        rendering_id=int(user["rendering_id"]),
        user_id=int(user["id"]),
        tags=user.get("tags", {}),
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        team=user["team"],
        timezone=parse_timezone(request),
    )
    return await decorated_fn(self, request)


def authenticate(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]]):
    async def wrapped2(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
        return await _authenticate(self, request, fn)

    return wrapped2


async def _authorize(
    action: str,
    self: "BoundResource",
    request: BoundRequestCollection,
    decorated_fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Any]],
):
    if action == "chart":
        await self.permission.can_chart(request)
    else:
        collection = request.foreign_collection if hasattr(request, "foreign_collection") else request.collection
        await self.permission.can(request.user, collection, f"{action}")

    return await decorated_fn(self, request)


def authorize(action: str):
    def wrapper(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Any]]):
        async def wrapped1(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
            return await _authorize(action, self, request, fn)

        return wrapped1

    return wrapper


async def _check_method(
    method: RequestMethod,
    self: "BoundResource",
    request: BoundRequestCollection,
    decorated_fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]],
):
    if request.method != method:
        return HttpResponseBuilder.build_method_not_allowed_response()
    return await decorated_fn(self, request)


def check_method(method: RequestMethod):
    def wrapper(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]]):
        async def wrapped(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
            return await _check_method(method, self, request, fn)

        return wrapped

    return wrapper


async def _ip_white_list(decorated_fn, self, request: Request, *args, **kwargs):
    try:
        await self.check_ip(request)
    except ForbiddenError as exc:
        return HttpResponseBuilder.build_client_error_response([exc])
    return await decorated_fn(self, request, *args, **kwargs)


def ip_white_list(decorated_fn):
    async def wrapped(self, request: Request, *args, **kwargs):
        return await _ip_white_list(decorated_fn, self, request, *args, **kwargs)

    return wrapped
