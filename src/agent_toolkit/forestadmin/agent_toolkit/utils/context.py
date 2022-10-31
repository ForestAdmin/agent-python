import enum
import json
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Dict, List, Optional


class RequestMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTION = "OPTION"


@dataclass
class User:
    rendering_id: int
    user_id: int
    tags: Dict[str, Any]
    email: str
    first_name: str
    last_name: str
    team: str


class Request:
    method: RequestMethod
    body: Optional[Dict[str, Any]] = None
    query: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    user: Optional[User] = None

    def __init__(
        self,
        method: RequestMethod,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        user: Optional[User] = None,
    ):
        self.method = method
        self.body = body
        self.query = query
        self.headers = headers
        self.user = user


@dataclass
class Response:
    status: int
    body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=lambda: {})


@dataclass
class FileResponse:
    file: Optional[BytesIO]
    name: str
    mimetype: str


def build_json_response(status: int, body: Dict[str, Any]):
    return Response(status, json.dumps(body), headers={"content-type": "application/json"})


def build_client_error_response(reasons: List[str]) -> Response:
    return build_json_response(
        400,
        {"errors": reasons},
    )


def build_success_response(body: Dict[str, Any]):
    return build_json_response(200, body)


def build_unknown_response():
    return Response(404)


def build_no_content_response():
    return Response(204)


def build_method_not_allowed_response():
    return Response(405)
