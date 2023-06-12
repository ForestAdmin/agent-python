import enum
import json
import sys
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo


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
    timezone: ZoneInfo
    # permission_level
    # role


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


def build_csv_response(body: str, filename: str) -> Response:
    return Response(
        200, body, headers={"content-type": "text/csv", "Content-Disposition": f'attachment; filename="{filename}"'}
    )


def build_success_response(body: Dict[str, Any]) -> Response:
    return build_json_response(200, body)


def build_unknown_response() -> Response:
    return Response(404)


def build_no_content_response() -> Response:
    return Response(204)


def build_method_not_allowed_response() -> Response:
    return Response(405)
