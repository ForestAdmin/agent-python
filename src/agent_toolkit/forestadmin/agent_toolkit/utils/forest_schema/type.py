import enum
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from typing_extensions import NotRequired

Number = Union[int, float]


class ValidationType(enum.Enum):
    PRESENT = "is present"
    GREATER_THAN = "is greater than"
    LESS_THAN = "is less than"
    BEFORE = "is before"
    AFTER = "is after"
    LONGER_THAN = "is longer than"
    SHORTER_THAN = "is shorter than"
    CONTAINS = "contains"
    LIKE = "is like"


class ServerValidationType(TypedDict):
    type: ValidationType
    value: Optional[Any]
    message: Optional[Any]


LiteralHasOne = Literal["HasOne"]
LiteralHasMany = Literal["HasMany"]
LiteralBelongsTo = Literal["BelongsTo"]
LiteralBelongsToMany = Literal["BelongsToMany"]

RelationServer = Union[LiteralHasOne, LiteralHasMany, LiteralBelongsTo, LiteralBelongsToMany]


class AgentStackMeta(TypedDict, total=False):
    engine: Literal["python"]
    engine_version: str
    database_type: str
    orm_version: str


class AgentMeta(TypedDict):
    liana: str
    liana_version: str
    stack: AgentStackMeta
    schemaFileHash: str


class ForestServerField(TypedDict, total=False):
    field: str
    type: ColumnAlias
    defaultValue: Any
    enums: Optional[List[str]]
    integration: None
    isFilterable: bool
    isPrimaryKey: bool
    isReadOnly: bool
    isRequired: bool
    isSortable: bool
    isVirtual: bool
    reference: Optional[str]
    inverseOf: Optional[str]
    relationship: RelationServer
    validations: List[ServerValidationType]


LiteralPage = Literal["page"]


class ForestServerActionHooks(TypedDict):
    load: bool
    change: List[Any]


class WidgetEditConfiguration(TypedDict):
    name: str
    parameters: Dict[str, Any]


# color
class ForestServerActionFieldColorPickerOptionsParameters(TypedDict):
    placeholder: Optional[str]
    enableOpacity: Optional[bool]
    quickPalette: Optional[List[str]]


class ForestServerActionFieldColorPickerOptions(TypedDict):
    name: Literal["color editor"]
    parameters: ForestServerActionFieldColorPickerOptionsParameters


# text
class ForestServerActionFieldTextEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]


class ForestServerActionFieldTextEditorOptions(TypedDict):
    name: Literal["text editor"]
    parameters: ForestServerActionFieldTextEditorOptionsParameters


# text list
class ForestServerActionFieldTextListEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]
    allowDuplicate: bool
    allowEmptyValue: bool
    enableReorder: bool


class ForestServerActionFieldTextListEditorOptions(TypedDict):
    name: Literal["input array"]
    parameters: ForestServerActionFieldTextListEditorOptionsParameters


# text area
class ForestServerActionFieldTextAreaEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]
    rows: NotRequired[str]


class ForestServerActionFieldTextAreaEditorOptions(TypedDict):
    name: Literal["text area editor"]
    parameters: ForestServerActionFieldTextAreaEditorOptionsParameters


# rich text
class ForestServerActionFieldRichTextEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]


class ForestServerActionFieldRichTextEditorOptions(TypedDict):
    name: Literal["rich text"]
    parameters: ForestServerActionFieldRichTextEditorOptionsParameters


# address
class ForestServerActionFieldAddressAutocompleteEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]


class ForestServerActionFieldAddressAutocompleteEditorOptions(TypedDict):
    name: Literal["address editor"]
    parameters: ForestServerActionFieldAddressAutocompleteEditorOptionsParameters


# number
class ForestServerActionFieldNumberInputEditorOptionsParameters(TypedDict):
    min: Optional[Number]
    max: Optional[Number]
    step: Optional[Number]


class ForestServerActionFieldNumberInputEditorOptions(TypedDict):
    name: Literal["address editor"]
    parameters: ForestServerActionFieldNumberInputEditorOptionsParameters


# number list
class ForestServerActionFieldNumberInputListEditorOptionsParameters(TypedDict):
    min: Optional[Number]
    max: Optional[Number]
    step: Optional[Number]
    placeholder: Optional[str]
    allowDuplicate: bool
    allowEmptyValue: bool
    enableReorder: bool


class ForestServerActionFieldNumberInputListEditorOptions(TypedDict):
    name: Literal["address editor"]
    parameters: ForestServerActionFieldNumberInputListEditorOptionsParameters


# currency
class ForestServerActionFieldCurrencyInputEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]
    min: Optional[Number]
    max: Optional[Number]
    step: Optional[Number]
    currency: str
    base: Literal["Unit", "Cent"]


class ForestServerActionFieldCurrencyInputEditorOptions(TypedDict):
    name: Literal["price editor"]
    parameters: ForestServerActionFieldCurrencyInputEditorOptionsParameters


# json
class ForestServerActionFieldJsonEditorEditorOptions(TypedDict):
    name: Literal["json code editor"]
    parameters: Dict[str, Any]


class ForestServerActionField(TypedDict):
    value: Any
    defaultValue: Any
    description: Optional[str]
    enums: Optional[List[str]]
    field: str
    hook: Optional[str]
    isReadOnly: bool
    isRequired: bool
    reference: Optional[str]
    type: Union[ColumnAlias, Literal["File"]]
    widget: Optional[Literal["belongsto select", "file picker"]]
    widgetEdit: Optional[WidgetEditConfiguration]


class ForestServerAction(TypedDict):
    id: str
    name: str
    type: Literal["single", "bulk", "global"]
    baseUrl: Optional[str]
    endpoint: str
    httpMethod: Literal["POST"]
    redirect: Any
    download: bool
    fields: List[ForestServerActionField]
    hooks: ForestServerActionHooks


class ForestServerSegment(TypedDict):
    id: str
    name: str


class ForestServerCollection(TypedDict):
    name: str
    icon: None
    integration: None
    isReadOnly: bool
    isSearchable: bool
    isVirtual: bool
    onlyForRelationships: bool
    paginationType: LiteralPage
    actions: Optional[List[ForestServerAction]]
    fields: List[ForestServerField]
    segments: Optional[List[ForestServerSegment]]


class ForestSchema(TypedDict):
    data: List[ForestServerCollection]
    meta: AgentMeta
