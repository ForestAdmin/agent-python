from typing import Any, Awaitable, Callable, TypeVar, Union

from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.services.permissions import PermissionServiceException
from forestadmin.agent_toolkit.utils.context import (
    FileResponse,
    Request,
    RequestMethod,
    Response,
    User,
    build_method_not_allowed_response,
)
from jose import JWTError, jwt

BoundRequest = TypeVar("BoundRequest", bound=Request)
BoundResource = TypeVar("BoundResource", bound=BaseCollectionResource)
BoundRequestCollection = TypeVar("BoundRequestCollection", bound=RequestCollection)


def authenticate(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]]):
    async def wrapped2(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
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
        )
        return await fn(self, request)

    return wrapped2


def authorize(action: str):
    def wrapper(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Any]]):
        async def wrapped1(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
            try:
                await self.permission.can(request, f"{action}:{request.collection.name}")
            except PermissionServiceException as e:
                return Response(status=e.STATUS, body=e.message)

            return await fn(self, request)

        return wrapped1

    return wrapper


def check_method(method: RequestMethod):
    def wrapper(fn: Callable[["BoundResource", BoundRequestCollection], Awaitable[Union[FileResponse, Response]]]):
        async def wrapped(self: "BoundResource", request: BoundRequestCollection) -> Union[FileResponse, Response]:
            if request.method != method:
                return build_method_not_allowed_response()
            return await fn(self, request)

        return wrapped

    return wrapper
