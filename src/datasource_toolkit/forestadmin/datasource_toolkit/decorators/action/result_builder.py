from io import IOBase
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import NotRequired, Self

OptionTypeAlias = Union[Literal["html"], Literal["text"]]
WebhookMethod = Union[Literal["GET"], Literal["POST"]]


class OptionAlias(TypedDict):
    type: NotRequired[OptionTypeAlias]
    invalidated: NotRequired[List[str]]


class ResultBuilder:
    SUCCESS = "Success"
    ERROR = "Error"
    WEBHOOK = "Webhook"
    FILE = "File"
    REDIRECT = "Redirect"

    def __init__(self) -> None:
        self.response_headers: Dict[str:str] = {}

    def set_header(self, name: str, value: str) -> Self:
        self.response_headers[name] = value

        return self

    def success(self, message: Optional[str] = None, options: Optional[OptionAlias] = None) -> ActionResult:
        if not options:
            options = {}

        return {
            "type": self.SUCCESS,
            "message": message or self.SUCCESS,
            "format": options.get("type", "text"),
            "invalidated": set(options.get("invalidated", [])),
            "response_headers": self.response_headers,
        }

    def error(self, message: Optional[str] = None, options: Optional[OptionAlias] = None) -> ActionResult:
        if not options:
            options = {}
        return {
            "type": self.ERROR,
            "message": message or self.ERROR,
            "format": options.get("type", "text"),
            "response_headers": self.response_headers,
        }

    def webhook(
        self,
        url: str,
        method: WebhookMethod = "POST",
        headers: Optional[RecordsDataAlias] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        return {
            "type": self.WEBHOOK,
            "url": url,
            "method": method,
            "headers": headers or {},
            "body": body or {},
            "response_headers": self.response_headers,
        }

    def file(self, file: IOBase, name: str = "file", mime_type: str = "text/plain") -> ActionResult:
        return {
            "type": self.FILE,
            "name": name,
            "mimeType": mime_type,
            "stream": file,
            "response_headers": self.response_headers,
        }

    def redirect(self, path: str) -> ActionResult:
        return {
            "type": self.REDIRECT,
            "path": path,
            "response_headers": self.response_headers,
        }
