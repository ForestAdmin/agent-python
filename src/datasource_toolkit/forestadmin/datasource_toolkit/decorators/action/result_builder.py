from io import BytesIO, IOBase, StringIO
from typing import Any, Dict, List, Literal, Optional, Union

from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from typing_extensions import NotRequired, Self, TypedDict

OptionTypeAlias = Literal["html", "text"]
WebhookMethod = Literal["GET", "POST"]


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
        self.response_headers: Dict[str, str] = {}

    def set_header(self, name: str, value: str) -> Self:
        """Add header to the action response

        Args:
            name (str): the header name
            value (str): the header value

        Returns:
            Self: self instance for chaining

        Example:
            .set_header("myHeaderName", "my header value")
        """
        self.response_headers[name] = value

        return self

    def success(self, message: Optional[str] = None, options: Optional[OptionAlias] = None) -> ActionResult:
        """Returns a success response from the action

        Args:
            message (str, optional): the success message to return. Defaults to None.
            options (dict, optional): available options to return. Defaults to None.

        Example:
            .success("Success", {"type": "html"})
        """
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
        """Returns an error response from the action

        Args:
            message (str, optional): the error message to return. Defaults to None.
            options (dict, optional): available options to return. Defaults to None.

        Example:
            .error("Failed to refund the customer!", {"type": "html"})
        """
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
        """Returns a webhook that the UI will trigger

        Args:
            url (str): the url of the webhook
            method (str, optional): the HTTP method of the webhook. Defaults to "POST".
            headers (dict, optional): a dict representing the list of headers to send with the webhook. Defaults to None
            body (dict, optional): a dict representing the body of the HTTP request. Defaults to None.

        Example:
            .webhook("http://my-company-name", "POST", {}, {"adminToken": "my-admin-token"})
        """
        return {
            "type": self.WEBHOOK,
            "url": url,
            "method": method,
            "headers": headers or {},
            "body": body or {},
            "response_headers": self.response_headers,
        }

    def file(self, file: Union[IOBase, str, bytes], name: str = "file", mime_type: str = "text/plain") -> ActionResult:
        """Returns a file that will be downloaded

        Args:
            file (IOBase): the actual file to download
            name (str, optional): the name of the file. Defaults to "file".
            mime_type (str, optional): the mime type of the file. Defaults to "text/plain".

        Example:
            .file("This is my file content", "download.txt", "text/plain")
        """
        if isinstance(file, str):
            stream = StringIO(file)
        elif isinstance(file, bytes):
            stream = BytesIO(file)
        else:
            stream = file
        return {
            "type": self.FILE,
            "name": name,
            "mimeType": mime_type,
            "stream": stream,
            "response_headers": self.response_headers,
        }

    def redirect(self, path: str) -> ActionResult:
        """Returns to the UI that a redirection is needed

        Args:
            path (str): the path to redirect to

        Example:
            .redirect("https://www.google.com")
        """
        return {
            "type": self.REDIRECT,
            "path": path,
            "response_headers": self.response_headers,
        }
