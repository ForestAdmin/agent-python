from datetime import date, datetime
from typing import Awaitable, Callable, Generic, List, Literal, TypeVar, Union

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
    LayoutWidgetTypes,
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


class PlainField(PlainFormElement, Generic[Result]):
    label: str
    description: NotRequired[ValueOrHandler[str]]
    is_required: NotRequired[ValueOrHandler[bool]]
    is_read_only: NotRequired[ValueOrHandler[bool]]
    value: NotRequired[ValueOrHandler[Result]]
    default_value: NotRequired[ValueOrHandler[Result]]


# layout
class PlainLayoutDynamicField(PlainFormElement):
    type: Literal[ActionFieldType.LAYOUT, "Layout"]


# collection
class PlainCollectionDynamicField(PlainField[CompositeIdAlias]):
    type: Literal[ActionFieldType.COLLECTION, "Collection"]
    collection_name: ValueOrHandler[str]


# enum
class PlainEnumDynamicField(PlainField[str]):
    type: Literal[ActionFieldType.ENUM, "Enum"]
    enum_values: ValueOrHandler[List[str]]
    if_: NotRequired[ValueOrHandler[bool]]


# enum list
class PlainListEnumDynamicField(PlainField[List[str]]):
    type: Literal[ActionFieldType.ENUM_LIST, "EnumList"]
    enum_values: ValueOrHandler[List[str]]


# boolean
class PlainBooleanDynamicField(PlainField[bool]):
    type: Literal[ActionFieldType.BOOLEAN, "Boolean"]


# date only
class PlainDateOnlyDynamicField(PlainField[date]):
    type: Literal[ActionFieldType.DATE_ONLY, "Dateonly"]


# datetime
class PlainDateTimeDynamicField(PlainField[datetime]):
    type: Literal[ActionFieldType.DATE, "Date"]


# time
class PlainTimeDynamicField(PlainField[str]):
    type: Literal[ActionFieldType.TIME, "Time"]


# number
class PlainNumberDynamicField(PlainField[Number]):
    type: Literal[ActionFieldType.NUMBER, "Number"]


# number list
class PlainListNumberDynamicField(PlainField[List[Number]]):
    type: Literal[ActionFieldType.NUMBER_LIST, "NumberList"]


# string
class PlainStringDynamicField(PlainField[str]):
    type: Literal[ActionFieldType.STRING, "String"]


# string list
class PlainStringListDynamicField(PlainField[List[str]]):
    type: Literal[ActionFieldType.STRING_LIST, "StringList"]


# json
class PlainJsonDynamicField(PlainField[str]):
    type: Literal[ActionFieldType.JSON, "Json"]


# file
class PlainFileDynamicField(PlainField[File]):
    type: Literal[ActionFieldType.FILE, "File"]


# file list
class PlainFileListDynamicField(PlainField[List[File]]):
    type: Literal[ActionFieldType.FILE_LIST, "FileList"]


##################################
# declare widget for field types #
##################################
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


class PlainLayoutRowConfiguration(PlainLayoutDynamicField, RowConfiguration):
    pass


class PlainLayoutSeparatorConfiguration(PlainLayoutDynamicField, SeparatorConfiguration):
    pass


class PlainLayoutPageConfiguration(PlainLayoutDynamicField, PageConfiguration):
    pass


class WidgetTyping(TypedDict):
    type: Union[ActionFieldType, ActionFieldTypeLiteral]
    widget: Union[WidgetTypes, LayoutWidgetTypes]
    search: Literal["static", "dynamic", "disabled"]


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
    # layout
    PlainLayoutRowConfiguration,
    PlainLayoutSeparatorConfiguration,
    PlainLayoutPageConfiguration,
    # for autocompletion
    WidgetTyping,  # this one must be the latest by name class (alphabetic order)
]

PlainDynamicLayoutElement = Union[
    # layout
    PlainLayoutRowConfiguration,
    PlainLayoutSeparatorConfiguration,
    PlainLayoutPageConfiguration,
]

PlainDynamicFormElement = Union[PlainDynamicLayoutElement, PlainDynamicField]
