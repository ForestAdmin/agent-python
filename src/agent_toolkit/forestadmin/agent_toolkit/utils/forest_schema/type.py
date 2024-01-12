import enum
from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from typing_extensions import NotRequired, TypedDict

Number = Union[int, float]
TValue = TypeVar("TValue")
TName = TypeVar("TName")


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


# file
class ForestServerActionFieldFilePickerEditorOptionsParameters(TypedDict):
    prefix: None
    filesExtensions: Optional[List[str]]
    filesSizeLimit: Optional[Number]
    filesCountLimit: Optional[Number]


class ForestServerActionFieldFilePickerEditorOptions(TypedDict):
    name: Literal["file picker"]
    parameters: ForestServerActionFieldFilePickerEditorOptionsParameters


# time
class ForestServerActionFieldTimePickerOptions(TypedDict):
    name: Literal["time editor"]
    parameters: Dict[str, Any]


# date
class ForestServerActionFieldDatePickerEditorOptionsParameters(TypedDict):
    placeholder: Optional[str]
    format: Optional[str]
    minDate: Optional[str]
    maxDate: Optional[str]


class ForestServerActionFieldDatePickerOptions(TypedDict):
    name: Literal["date editor"]
    parameters: ForestServerActionFieldDatePickerEditorOptionsParameters


# checkbox
class ForestServerActionFieldCheckboxOptions(TypedDict):
    name: Literal["boolean editor"]
    parameters: Dict[str, Any]


# base group value
class OptionWithLabel(TypedDict, Generic[TValue]):
    label: str
    value: Optional[TValue]


class ForestServerActionFieldLimitedValueOptionsParameterStatic(TypedDict, Generic[TValue]):
    options: Union[List[OptionWithLabel[TValue]], List[TValue]]


class ForestServerActionFieldLimitedValueOptionsParameters(TypedDict, Generic[TValue]):
    static: ForestServerActionFieldLimitedValueOptionsParameterStatic[TValue]


class ForestServerActionFieldLimitedValueOptions(TypedDict, Generic[TName, TValue]):
    name: TName
    parameters: ForestServerActionFieldLimitedValueOptionsParameters[TValue]


# radio group
ForestServerActionFieldRadioGroupOptions = ForestServerActionFieldLimitedValueOptions[Literal["radio button"], TValue]

# checkbox group
ForestServerActionFieldCheckboxGroupOptions = ForestServerActionFieldLimitedValueOptions[Literal["checkboxes"], TValue]


# dropdown
class ForestServerActionFieldDropdownOptionsParameters(TypedDict, Generic[TValue]):
    placeholder: Optional[str]
    isSearchable: Optional[bool]
    searchType: Optional[Literal["dynamic"]]
    static: ForestServerActionFieldLimitedValueOptionsParameterStatic[TValue]


class ForestServerActionFieldDropdownOptions(TypedDict, Generic[TValue]):
    name: Literal["dropdown"]
    parameters: ForestServerActionFieldDropdownOptionsParameters[TValue]


# user dropdown
class ForestServerActionFieldUserDropdownOptionsParameters(TypedDict):
    placeholder: Optional[str]


class ForestServerActionFieldUserDropdownOptions(TypedDict):
    name: Literal["assignee editor"]
    parameters: ForestServerActionFieldUserDropdownOptionsParameters


WidgetEditConfiguration = Union[
    ForestServerActionFieldColorPickerOptions,
    ForestServerActionFieldTextEditorOptions,
    ForestServerActionFieldTextListEditorOptions,
    ForestServerActionFieldTextAreaEditorOptions,
    ForestServerActionFieldRichTextEditorOptions,
    ForestServerActionFieldAddressAutocompleteEditorOptions,
    ForestServerActionFieldNumberInputEditorOptions,
    ForestServerActionFieldNumberInputListEditorOptions,
    ForestServerActionFieldCurrencyInputEditorOptions,
    ForestServerActionFieldJsonEditorEditorOptions,
    ForestServerActionFieldFilePickerEditorOptions,
    ForestServerActionFieldTimePickerOptions,
    ForestServerActionFieldDatePickerOptions,
    ForestServerActionFieldCheckboxOptions,
    ForestServerActionFieldRadioGroupOptions,
    ForestServerActionFieldCheckboxGroupOptions,
    ForestServerActionFieldDropdownOptions,
    ForestServerActionFieldUserDropdownOptions,
]


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
    searchValue: Optional[str]


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
    searchField: Optional[str]


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
