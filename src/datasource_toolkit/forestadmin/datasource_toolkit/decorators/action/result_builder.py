from io import IOBase
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import NotRequired

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

    @classmethod
    def success(cls, message: Optional[str] = None, options: Optional[OptionAlias] = None) -> ActionResult:
        if not options:
            options = {}

        return {
            "type": cls.SUCCESS,
            "message": message or cls.SUCCESS,
            "format": options.get("type", "text"),
            "invalidated": set(options.get("invalidated", [])),
        }

    @classmethod
    def error(cls, message: Optional[str] = None, options: Optional[OptionAlias] = None) -> ActionResult:
        if not options:
            options = {}
        return {
            "type": cls.ERROR,
            "message": message or cls.ERROR,
            "format": options.get("type", "text"),
        }

    @classmethod
    def webhook(
        cls,
        url: str,
        method: WebhookMethod = "POST",
        headers: Optional[RecordsDataAlias] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        return {"type": cls.WEBHOOK, "url": url, "method": method, "headers": headers or {}, "body": body or {}}

    @classmethod
    def file(cls, file: IOBase, name: str = "file", mime_type: str = "text/plain") -> ActionResult:
        return {"type": cls.FILE, "name": name, "mimeType": mime_type, "stream": file}

    @classmethod
    def redirect(cls, path: str) -> ActionResult:
        return {"type": cls.REDIRECT, "path": path}
