import enum
import json
import sys
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError

if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo

from forestadmin.datasource_toolkit.exceptions import BusinessError, ForbiddenError, UnprocessableError, ValidationError


class RequestMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"


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
    client_ip: Optional[str] = None

    def __init__(
        self,
        method: RequestMethod,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        user: Optional[User] = None,
        client_ip: Optional[str] = None,
    ):
        self.method = method
        self.body = body
        self.query = query
        self.headers = headers
        self.user = user
        self.client_ip = client_ip


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
    headers: Dict[str, str] = field(default_factory=lambda: {})


class HttpResponseBuilder:
    _ERROR_MESSAGE_CUSTOMIZER: Callable[[Exception], str] = None

    @classmethod
    def setup_error_message_customizer(cls, customizer_function: Callable[[Exception], str]):
        cls._ERROR_MESSAGE_CUSTOMIZER = customizer_function

    @staticmethod
    def build_json_response(status: int, body: Dict[str, Any]) -> Response:
        return Response(status, json.dumps(body), headers={"content-type": "application/json"})

    @staticmethod
    def build_client_error_response(reasons: List[Exception]) -> Response:
        errors = []
        for error in reasons:
            tmp = {
                "name": HttpResponseBuilder._get_error_name(error),
                "detail": HttpResponseBuilder._get_error_message(error),
                "status": HttpResponseBuilder._get_error_status(error),
            }
            if hasattr(error, "data") and getattr(error, "data") is not None:
                tmp["data"] = error.data

            errors.append(tmp)

        return HttpResponseBuilder.build_json_response(
            HttpResponseBuilder._get_error_status(reasons[0]),
            {"errors": errors},
        )

    @staticmethod
    def build_csv_response(body: str, filename: str) -> Response:
        return Response(
            200, body, headers={"content-type": "text/csv", "Content-Disposition": f'attachment; filename="{filename}"'}
        )

    @staticmethod
    def build_success_response(body: Dict[str, Any]) -> Response:
        return HttpResponseBuilder.build_json_response(200, body)

    @staticmethod
    def build_unknown_response() -> Response:
        return Response(404)

    @staticmethod
    def build_no_content_response() -> Response:
        return Response(204)

    @staticmethod
    def build_method_not_allowed_response() -> Response:
        return Response(405)

    @staticmethod
    def _get_error_status(error: Exception):
        if isinstance(error, ValidationError):
            return 400
        if isinstance(error, ForbiddenError):
            return 403
        if isinstance(error, UnprocessableError):
            return 422
        if isinstance(error, HTTPError):
            return error.code

        return 500

    @staticmethod
    def _get_error_message(error: Exception):
        if isinstance(error, BusinessError):
            return str(error.args[0][3:])

        if HttpResponseBuilder._ERROR_MESSAGE_CUSTOMIZER is not None:
            return HttpResponseBuilder._ERROR_MESSAGE_CUSTOMIZER(error)
        else:
            return str(error)

    @staticmethod
    def _get_error_name(error: Exception):
        if hasattr(error, "name") and getattr(error, "name") is not None:
            return error.name
        else:
            return error.__class__.__name__
