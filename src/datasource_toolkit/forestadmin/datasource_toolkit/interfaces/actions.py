import enum
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Set, TypedDict, Union


class ActionsScope(enum.Enum):
    SINGLE = "single"
    BULK = "bulk"
    GLOBAL = "global"


@dataclass
class File:
    mime_type: str
    buffer: str
    name: str
    charset: Optional[str] = None


@dataclass
class Action:
    scope: ActionsScope
    generate_file: Optional[bool]
    static_form: Optional[bool]


class ActionFieldType(enum.Enum):
    BOOLEAN = "Boolean"
    COLLECTION = "Collection"
    DATE = "Date"
    DATE_ONLY = "Dateonly"
    ENUM = "Enum"
    FILE = "File"
    JSON = "Json"
    NUMBER = "Number"
    STRING = "String"
    ENUM_LIST = "EnumList"
    FILE_LIST = "FileList"
    NUMBER_LIST = "NumberList"
    STRING_LIST = "StringList"


class ActionField(TypedDict):
    type: ActionFieldType
    label: str
    description: Optional[str]
    is_required: Optional[bool]
    is_read_only: Optional[bool]
    value: Optional[Any]
    default_value: Optional[Any]
    watch_changes: bool
    enum_values: Optional[List[str]]
    collection_name: Optional[str]


class SuccessResult(TypedDict):
    type: Literal["Success"]
    message: str
    format: Union[Literal["html"], Literal["text"]]
    invalidated: Set[str]


class ErrorResult(TypedDict):
    type: Literal["Error"]
    message: str
    format: Union[Literal["html"], Literal["text"]]


class WebHookResult(TypedDict):
    type: Literal["Webhook"]
    url: str
    method: Union[Literal["GET"], Literal["POST"]]
    headers: Dict[str, str]
    body: Any


class FileResult(TypedDict):
    type: Literal["File"]
    mimeType: str
    name: str
    stream: Any


class RedirectResult(TypedDict):
    type: Literal["Redirect"]
    path: str


ActionResult = Union[SuccessResult, ErrorResult, WebHookResult, FileResult, RedirectResult]
