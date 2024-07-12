import enum
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Set, Union

from typing_extensions import NotRequired, TypedDict

Number = Union[int, float]


class ActionsScope(enum.Enum):
    SINGLE = "Single"
    BULK = "Bulk"
    GLOBAL = "Global"


ActionScopeLiteral = Literal["Single", "Bulk", "Global"]


@dataclass
class File:
    mime_type: str
    buffer: bytes
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
    TIME = "Time"
    ENUM = "Enum"
    FILE = "File"
    JSON = "Json"
    NUMBER = "Number"
    STRING = "String"
    ENUM_LIST = "EnumList"
    FILE_LIST = "FileList"
    NUMBER_LIST = "NumberList"
    STRING_LIST = "StringList"


ActionFieldTypeLiteral = Literal[
    "Boolean",
    "Collection",
    "Date",
    "Dateonly",
    "Time",
    "Enum",
    "File",
    "Json",
    "Number",
    "String",
    "EnumList",
    "FileList",
    "NumberList",
    "StringList",
]


WidgetTypes = Literal[
    "TimePicker",
    "TextInputList",
    "TextInput",
    "TextArea",
    "RichText",
    "NumberInputList",
    "NumberInput",
    "JsonEditor",
    "FilePicker",
    "DatePicker",
    "CurrencyInput",
    "Checkbox",
    "ColorPicker",
    "AddressAutocomplete",
    "RadioGroup",
    "CheckboxGroup",
    "Dropdown",
    "UserDropdown",
]


class ActionField(TypedDict):
    type: ActionFieldType
    label: str
    description: NotRequired[Optional[str]]
    is_required: NotRequired[Optional[bool]]
    is_read_only: NotRequired[Optional[bool]]
    value: NotRequired[Optional[Any]]
    default_value: NotRequired[Optional[Any]]
    watch_changes: bool
    enum_values: NotRequired[Optional[List[str]]]
    collection_name: NotRequired[Optional[str]]
    widget: NotRequired[WidgetTypes]
    max: NotRequired[Number]
    min: NotRequired[Number]
    step: NotRequired[Number]
    base: NotRequired[Literal["Cent", "Unit"]]
    allow_duplicates: NotRequired[bool]
    quick_palette: NotRequired[List[str]]
    format: NotRequired[str]
    extensions: NotRequired[List[str]]
    enable_reorder: NotRequired[bool]
    options: NotRequired[Any]
    max_size_mb: NotRequired[Number]
    currency: NotRequired[str]
    enable_opacity: NotRequired[bool]
    rows: NotRequired[Number]
    placeholder: NotRequired[str]
    max_count: NotRequired[int]
    search: NotRequired[Any]
    allow_empty_values: NotRequired[bool]


class SuccessResult(TypedDict):
    type: Literal["Success"]
    message: str
    format: Literal["html", "text"]
    invalidated: Set[str]
    response_headers: Optional[Dict[str, str]]


class ErrorResult(TypedDict):
    type: Literal["Error"]
    message: str
    format: Literal["html", "text"]
    response_headers: Optional[Dict[str, str]]


class WebHookResult(TypedDict):
    type: Literal["Webhook"]
    url: str
    method: Literal["GET", "POST"]
    headers: Dict[str, str]
    body: Any
    response_headers: Optional[Dict[str, str]]


class FileResult(TypedDict):
    type: Literal["File"]
    mimeType: str
    name: str
    stream: Any
    response_headers: Optional[Dict[str, str]]


class RedirectResult(TypedDict):
    type: Literal["Redirect"]
    path: str
    response_headers: Optional[Dict[str, str]]


ActionResult = Union[SuccessResult, ErrorResult, WebHookResult, FileResult, RedirectResult]
