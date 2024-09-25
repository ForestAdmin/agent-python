from datetime import date, datetime
from typing import Awaitable, Callable, List, Literal, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.types.widgets import (
    AddressAutocompleteFieldConfiguration,
    ArrayTextInputFieldConfiguration,
    CheckboxesFieldConfiguration,
    CheckboxFieldConfiguration,
    ColorPickerFieldConfiguration,
    CurrencyInputFieldConfiguration,
    DatePickerFieldConfiguration,
    DropdownDynamicFieldConfiguration,
    DropdownDynamicSearchFieldConfiguration,
    FileListPickerFieldConfiguration,
    FilePickerFieldConfiguration,
    HtmlBlockConfiguration,
    JsonEditorFieldConfiguration,
    NumberInputFieldConfiguration,
    NumberInputListFieldConfiguration,
    PageConfiguration,
    RadioButtonFieldConfiguration,
    RichTextFieldConfiguration,
    RowConfiguration,
    SeparatorConfiguration,
    TextAreaFieldConfiguration,
    TextInputFieldConfiguration,
    TimePickerFieldConfiguration,
    UserDropdownFieldConfiguration,
)
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionFieldType,
    ActionFieldTypeLiteral,
    File,
    LayoutComponentTypes,
    WidgetTypes,
)
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from typing_extensions import NotRequired, TypedDict

Number = Union[int, float]
Context = Union[ActionContext, ActionContextSingle, ActionContextBulk]
Result = TypeVar("Result")

ValueOrHandler = Union[
    Callable[[ActionContext], Union[Awaitable[Result], Result]],
    Callable[[ActionContextSingle], Union[Awaitable[Result], Result]],
    Callable[[ActionContextBulk], Union[Awaitable[Result], Result]],
    Result,
]


class PlainFormElement(TypedDict):
    if_: NotRequired[ValueOrHandler[bool]]


class PlainField(PlainFormElement):
    label: str
    id: NotRequired[str]
    description: NotRequired[ValueOrHandler[str]]
    is_required: NotRequired[ValueOrHandler[bool]]
    is_read_only: NotRequired[ValueOrHandler[bool]]


class PlainCollectionDynamicField(PlainField):
    type: Literal[ActionFieldType.COLLECTION, "Collection"]
    collection_name: ValueOrHandler[str]
    value: NotRequired[ValueOrHandler[CompositeIdAlias]]
    default_value: NotRequired[ValueOrHandler[CompositeIdAlias]]


# collection
# enum
class PlainEnumDynamicField(PlainField):
    type: Literal[ActionFieldType.ENUM, "Enum"]
    enum_values: ValueOrHandler[List[str]]
    if_: NotRequired[ValueOrHandler[bool]]
    value: NotRequired[ValueOrHandler[str]]
    default_value: NotRequired[ValueOrHandler[str]]


# enum list
class PlainListEnumDynamicField(PlainField):
    type: Literal[ActionFieldType.ENUM_LIST, "EnumList"]
    enum_values: ValueOrHandler[List[str]]
    value: NotRequired[ValueOrHandler[List[str]]]
    default_value: NotRequired[ValueOrHandler[List[str]]]


# boolean
class PlainBooleanDynamicField(PlainField):
    type: Literal[ActionFieldType.BOOLEAN, "Boolean"]
    value: NotRequired[ValueOrHandler[bool]]
    default_value: NotRequired[ValueOrHandler[bool]]


# date only
class PlainDateOnlyDynamicField(PlainField):
    type: Literal[ActionFieldType.DATE_ONLY, "Dateonly"]
    value: NotRequired[ValueOrHandler[date]]
    default_value: NotRequired[ValueOrHandler[date]]


# datetime
class PlainDateTimeDynamicField(PlainField):
    type: Literal[ActionFieldType.DATE, "Date"]
    value: NotRequired[ValueOrHandler[datetime]]
    default_value: NotRequired[ValueOrHandler[datetime]]


# time
class PlainTimeDynamicField(PlainField):
    type: Literal[ActionFieldType.TIME, "Time"]
    value: NotRequired[ValueOrHandler[str]]
    default_value: NotRequired[ValueOrHandler[str]]


# number
class PlainNumberDynamicField(PlainField):
    type: Literal[ActionFieldType.NUMBER, "Number"]
    value: NotRequired[ValueOrHandler[Number]]
    default_value: NotRequired[ValueOrHandler[Number]]


# number list
class PlainListNumberDynamicField(PlainField):
    type: Literal[ActionFieldType.NUMBER_LIST, "NumberList"]
    value: NotRequired[ValueOrHandler[Number]]
    default_value: NotRequired[ValueOrHandler[Number]]


# string
class PlainStringDynamicField(PlainField):
    type: Literal[ActionFieldType.STRING, "String"]
    value: NotRequired[ValueOrHandler[str]]
    default_value: NotRequired[ValueOrHandler[str]]


# string list
class PlainStringListDynamicField(PlainField):
    type: Literal[ActionFieldType.STRING_LIST, "StringList"]
    value: NotRequired[ValueOrHandler[List[str]]]
    default_value: NotRequired[ValueOrHandler[List[str]]]


# json
class PlainJsonDynamicField(PlainField):
    type: Literal[ActionFieldType.JSON, "Json"]
    value: NotRequired[ValueOrHandler[str]]
    default_value: NotRequired[ValueOrHandler[str]]


# file
class PlainFileDynamicField(PlainField):
    type: Literal[ActionFieldType.FILE, "File"]
    value: NotRequired[ValueOrHandler[File]]
    default_value: NotRequired[ValueOrHandler[File]]


# file list
class PlainFileListDynamicField(PlainField):
    type: Literal[ActionFieldType.FILE_LIST, "FileList"]
    value: NotRequired[ValueOrHandler[List[File]]]
    default_value: NotRequired[ValueOrHandler[List[File]]]


# Layout
class PlainLayoutDynamicFormElement(PlainFormElement):
    type: Literal[ActionFieldType.LAYOUT, "Layout"]


# declare widget for field types
class PlainStringDynamicFieldColorWidget(PlainStringDynamicField, ColorPickerFieldConfiguration):
    pass


class PlainStringDynamicFieldTextInputWidget(PlainStringDynamicField, TextInputFieldConfiguration):
    pass


class PlainStringDynamicFieldTextAreaWidget(PlainStringDynamicField, TextAreaFieldConfiguration):
    pass


class PlainStringDynamicFieldRichTextWidget(PlainStringDynamicField, RichTextFieldConfiguration):
    pass


class PlainStringDynamicFieldAddressAutocompleteWidget(PlainStringDynamicField, AddressAutocompleteFieldConfiguration):
    pass


class PlainStringListDynamicFieldTextInputListWidget(PlainStringListDynamicField, ArrayTextInputFieldConfiguration):
    pass


class PlainNumberDynamicFieldNumberInputWidget(PlainNumberDynamicField, NumberInputFieldConfiguration):
    pass


class PlainNumberDynamicFieldCurrencyInputWidget(PlainNumberDynamicField, CurrencyInputFieldConfiguration):
    pass


class PlainListNumberDynamicFieldNumberInputListWidget(PlainListNumberDynamicField, NumberInputListFieldConfiguration):
    pass


class PlainJsonDynamicFieldJsonEditorWidget(PlainJsonDynamicField, JsonEditorFieldConfiguration):
    pass


class PlainFileDynamicFieldFilePickerWidget(PlainFileDynamicField, FilePickerFieldConfiguration):
    pass


class PlainFileListDynamicFieldFilePickerWidget(PlainFileListDynamicField, FileListPickerFieldConfiguration):
    pass


class PlainDateDynamicFieldDatePickerWidget(PlainDateTimeDynamicField, DatePickerFieldConfiguration):
    pass


class PlainDateOnlyDynamicFieldDatePickerWidget(PlainDateOnlyDynamicField, DatePickerFieldConfiguration):
    pass


class PlainTimeDynamicFieldTimePickerWidget(PlainTimeDynamicField, TimePickerFieldConfiguration):
    pass


class PlainBooleanDynamicFieldCheckboxWidget(PlainBooleanDynamicField, CheckboxFieldConfiguration):
    pass


class PlainStringDynamicFieldRadioButtonWidget(PlainStringDynamicField, RadioButtonFieldConfiguration[str]):
    pass


class PlainNumberDynamicFieldRadioButtonWidget(PlainNumberDynamicField, RadioButtonFieldConfiguration[Number]):
    pass


class PlainStringListDynamicFieldRadioButtonWidget(PlainStringListDynamicField, CheckboxesFieldConfiguration[str]):
    pass


class PlainListNumberDynamicFieldRadioButtonWidget(PlainListNumberDynamicField, CheckboxesFieldConfiguration[Number]):
    pass


class PlainNumberDynamicFieldDropdownWidget(PlainNumberDynamicField, DropdownDynamicFieldConfiguration[Number]):
    pass


class PlainListNumberDynamicFieldDropdownWidget(PlainListNumberDynamicField, DropdownDynamicFieldConfiguration[Number]):
    pass


class PlainStringDynamicFieldDropdownWidget(PlainStringDynamicField, DropdownDynamicFieldConfiguration[str]):
    pass


class PlainStringListDynamicFieldDropdownWidget(PlainStringListDynamicField, DropdownDynamicFieldConfiguration[str]):
    pass


class PlainNumberDynamicFieldDropdownSearchWidget(
    PlainNumberDynamicField, DropdownDynamicSearchFieldConfiguration[Number]
):
    pass


class PlainListNumberDynamicFieldDropdownSearchWidget(
    PlainListNumberDynamicField, DropdownDynamicSearchFieldConfiguration[Number]
):
    pass


class PlainStringDynamicFieldDropdownSearchWidget(
    PlainStringDynamicField, DropdownDynamicSearchFieldConfiguration[str]
):
    pass


class PlainStringListDynamicFieldDropdownSearchWidget(
    PlainStringListDynamicField, DropdownDynamicSearchFieldConfiguration[str]
):
    pass


# user dropdown
class PlainStringListDynamicFieldUserDropdownFieldConfiguration(
    PlainStringListDynamicField, UserDropdownFieldConfiguration
):
    pass


class PlainStringDynamicFieldUserDropdownFieldConfiguration(PlainStringDynamicField, UserDropdownFieldConfiguration):
    pass


class PlainLayoutDynamicLayoutElementSeparator(PlainLayoutDynamicFormElement, SeparatorConfiguration):
    pass


class PlainLayoutDynamicLayoutElementHtmlBlock(PlainLayoutDynamicFormElement, HtmlBlockConfiguration):
    pass


class PlainLayoutDynamicLayoutElementRow(PlainLayoutDynamicFormElement, RowConfiguration):
    pass


class PlainLayoutDynamicLayoutElementPage(PlainLayoutDynamicFormElement, PageConfiguration):
    pass


# If I split PlainTyping into multiple ones, auto completion stop working.
# I dunno why, but like this it works!!! So let's not touch it
class PlainTyping(TypedDict):
    type: Union[ActionFieldType, ActionFieldTypeLiteral]
    widget: WidgetTypes
    search: Literal["static", "dynamic", "disabled"]
    component: LayoutComponentTypes


PlainDynamicField = Union[
    # boolean
    PlainBooleanDynamicField,
    PlainBooleanDynamicFieldCheckboxWidget,
    # collection
    PlainCollectionDynamicField,
    # enum
    PlainEnumDynamicField,
    PlainListEnumDynamicField,
    # number & widgets
    PlainNumberDynamicField,
    PlainNumberDynamicFieldNumberInputWidget,
    PlainNumberDynamicFieldCurrencyInputWidget,
    PlainNumberDynamicFieldRadioButtonWidget,
    PlainNumberDynamicFieldDropdownWidget,
    PlainNumberDynamicFieldDropdownSearchWidget,
    # number list & widgets
    PlainListNumberDynamicField,
    PlainListNumberDynamicFieldNumberInputListWidget,
    PlainListNumberDynamicFieldRadioButtonWidget,
    PlainListNumberDynamicFieldDropdownWidget,
    PlainListNumberDynamicFieldDropdownSearchWidget,
    # string & widgets
    PlainStringDynamicField,
    PlainStringDynamicFieldColorWidget,
    PlainStringDynamicFieldTextInputWidget,
    PlainStringDynamicFieldTextAreaWidget,
    PlainStringDynamicFieldRichTextWidget,
    PlainStringDynamicFieldAddressAutocompleteWidget,
    PlainStringDynamicFieldRadioButtonWidget,
    PlainStringDynamicFieldDropdownWidget,
    PlainStringDynamicFieldDropdownSearchWidget,
    PlainStringDynamicFieldUserDropdownFieldConfiguration,
    # string list & widgets
    PlainStringListDynamicField,
    PlainStringListDynamicFieldTextInputListWidget,
    PlainStringListDynamicFieldRadioButtonWidget,
    PlainStringListDynamicFieldDropdownWidget,
    PlainStringListDynamicFieldDropdownSearchWidget,
    PlainStringListDynamicFieldUserDropdownFieldConfiguration,
    # json
    PlainJsonDynamicField,
    PlainJsonDynamicFieldJsonEditorWidget,
    # file
    PlainFileDynamicField,
    PlainFileDynamicFieldFilePickerWidget,
    # file list
    PlainFileListDynamicField,
    PlainFileListDynamicFieldFilePickerWidget,
    # date
    PlainDateTimeDynamicField,
    PlainDateDynamicFieldDatePickerWidget,
    # date only
    PlainDateOnlyDynamicField,
    PlainDateDynamicFieldDatePickerWidget,
    # time
    PlainTimeDynamicField,
    PlainTimeDynamicFieldTimePickerWidget,
    # for autocompletion
    PlainTyping,  # this one must be the latest by name class (alphabetic order)
]

PlainDynamicLayout = Union[
    # Layout
    PlainLayoutDynamicLayoutElementSeparator,
    PlainLayoutDynamicLayoutElementHtmlBlock,
    PlainLayoutDynamicLayoutElementRow,
    PlainLayoutDynamicLayoutElementPage,
    # for autocompletion
    PlainTyping,  # this one must be the latest by name class (alphabetic order)
]

PlainDynamicFormElement = Union[PlainDynamicField, PlainDynamicLayout]
