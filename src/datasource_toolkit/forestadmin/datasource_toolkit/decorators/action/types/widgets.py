from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Awaitable, Callable, Generic, List, Literal, Optional, Set, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    # avoid circular import for typing (also with 'from __future__ import annotations')
    # https://stackoverflow.com/questions/61544854/from-future-import-annotations
    from forestadmin.datasource_toolkit.decorators.action.form_elements import BaseDynamicField, BaseDynamicFormElement
    from forestadmin.datasource_toolkit.decorators.action.types.fields import PlainDynamicField, PlainDynamicFormElement

Number = Union[int, float]

Context = Union[ActionContext, ActionContextSingle, ActionContextBulk]
Result = TypeVar("Result")

TWidget = TypeVar("TWidget")
TValue = TypeVar("TValue")

ValueOrHandler = Union[
    Callable[[ActionContext], Union[Awaitable[Result], Result]],
    Callable[[ActionContextSingle], Union[Awaitable[Result], Result]],
    Callable[[ActionContextBulk], Union[Awaitable[Result], Result]],
    Result,
]


class ColorPickerFieldConfiguration(TypedDict):
    widget: Literal["ColorPicker"]
    placeholder: Optional[str]
    enable_opacity: Optional[bool]
    quick_palette: Optional[List[str]]


class TextInputFieldConfiguration(TypedDict):
    widget: Literal["TextInput"]
    placeholder: NotRequired[str]


class TextAreaFieldConfiguration(TypedDict):
    widget: Literal["TextArea"]
    placeholder: NotRequired[Optional[str]]
    rows: NotRequired[int]


class RichTextFieldConfiguration(TypedDict):
    widget: Literal["RichText"]
    placeholder: NotRequired[Optional[str]]


class AddressAutocompleteFieldConfiguration(TypedDict):
    widget: Literal["AddressAutocomplete"]
    placeholder: NotRequired[Optional[str]]


class ArrayTextInputFieldConfiguration(TypedDict):
    widget: Literal["TextInputList"]
    placeholder: NotRequired[Optional[str]]
    enable_reorder: NotRequired[Optional[bool]]
    allow_empty_values: NotRequired[Optional[bool]]
    allow_duplicates: NotRequired[Optional[bool]]


class NumberInputFieldConfiguration(TypedDict):
    widget: Literal["NumberInput"]
    min: NotRequired[Optional[ValueOrHandler[Number]]]
    max: NotRequired[Optional[ValueOrHandler[Number]]]
    step: NotRequired[Optional[ValueOrHandler[Number]]]


class NumberInputListFieldConfiguration(TypedDict):
    widget: Literal["NumberInputList"]
    min: NotRequired[Optional[ValueOrHandler[Number]]]
    max: NotRequired[Optional[ValueOrHandler[Number]]]
    step: NotRequired[Optional[ValueOrHandler[Number]]]
    placeholder: NotRequired[Optional[str]]
    enable_reorder: NotRequired[Optional[bool]]
    allow_duplicates: NotRequired[Optional[bool]]


class CurrencyInputFieldConfiguration(TypedDict):
    widget: Literal["CurrencyInput"]
    placeholder: NotRequired[Optional[str]]
    currency: NotRequired[Optional[str]]
    base: NotRequired[Optional[ValueOrHandler[Literal["Unit", "Cent"]]]]
    min: NotRequired[Optional[ValueOrHandler[Number]]]
    max: NotRequired[Optional[ValueOrHandler[Number]]]
    step: NotRequired[Optional[ValueOrHandler[Number]]]


class JsonEditorFieldConfiguration(TypedDict):
    widget: Literal["JsonEditor"]


class FilePickerFieldConfiguration(TypedDict):
    widget: Literal["FilePicker"]
    extensions: NotRequired[Optional[ValueOrHandler[List[str]]]]
    max_size_mb: NotRequired[Optional[ValueOrHandler[Number]]]


class FileListPickerFieldConfiguration(TypedDict):
    widget: Literal["FilePicker"]
    extensions: NotRequired[Optional[ValueOrHandler[List[str]]]]
    max_size_mb: NotRequired[Optional[ValueOrHandler[Number]]]
    max_count: NotRequired[Optional[ValueOrHandler[Number]]]


class TimePickerFieldConfiguration(TypedDict):
    widget: Literal["TimePicker"]


class DatePickerFieldConfiguration(TypedDict):
    widget: Literal["DatePicker"]
    placeholder: NotRequired[Optional[str]]
    format: NotRequired[Optional[ValueOrHandler[str]]]
    min: NotRequired[Optional[ValueOrHandler[date]]]
    max: NotRequired[Optional[ValueOrHandler[date]]]


class CheckboxFieldConfiguration(TypedDict):
    widget: Literal["Checkbox"]


class DropdownOptionWithLabel(TypedDict, Generic[TValue]):
    label: str
    value: Optional[TValue]


DropdownOption = Union[TValue, DropdownOptionWithLabel[TValue]]

SearchOptionHandler = Callable[
    [Context, str], Union[List[DropdownOption[TValue]], Awaitable[List[DropdownOption[TValue]]]]
]


class LimitedValueDynamicFieldConfiguration(TypedDict, Generic[TWidget, TValue]):
    widget: TWidget
    options: Union[
        List[DropdownOption], Callable[[Context], Union[List[DropdownOption], Awaitable[List[DropdownOption]]]]
    ]


class RadioButtonFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["RadioGroup"], TValue]):
    pass


class CheckboxesFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["CheckboxGroup"], TValue]):
    pass


class DropdownDynamicFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["Dropdown"], TValue]):
    placeholder: NotRequired[Optional[str]]
    search: NotRequired[Optional[Literal["static", "disabled"]]]


class DropdownDynamicSearchFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["Dropdown"], TValue]):
    placeholder: NotRequired[Optional[str]]
    search: Literal["dynamic"]
    options: SearchOptionHandler[TValue]  # type: ignore


class UserDropdownFieldConfiguration(TypedDict):
    widget: Literal["UserDropdown"]
    placeholder: NotRequired[Optional[str]]


class SeparatorConfiguration(TypedDict):
    component: Literal["Separator"]


class HtmlBlockConfiguration(TypedDict):
    component: Literal["HtmlBlock"]
    content: ValueOrHandler[str]


class RowConfiguration(TypedDict):
    component: Literal["Row"]
    fields: List[Union[PlainDynamicField, BaseDynamicField]]


class PageConfiguration(TypedDict):
    component: Literal["Page"]
    elements: List[Union[PlainDynamicFormElement, BaseDynamicFormElement]]
    next_button_label: NotRequired[str]
    previous_button_label: NotRequired[str]


WIDGET_ATTRIBUTES: Set[str] = set()
for WidgetType in [
    ColorPickerFieldConfiguration,
    TextInputFieldConfiguration,
    TextAreaFieldConfiguration,
    RichTextFieldConfiguration,
    AddressAutocompleteFieldConfiguration,
    ArrayTextInputFieldConfiguration,
    NumberInputFieldConfiguration,
    NumberInputListFieldConfiguration,
    CurrencyInputFieldConfiguration,
    JsonEditorFieldConfiguration,
    FilePickerFieldConfiguration,
    FileListPickerFieldConfiguration,
    DatePickerFieldConfiguration,
    TimePickerFieldConfiguration,
    CheckboxFieldConfiguration,
    CheckboxesFieldConfiguration,
    RadioButtonFieldConfiguration,
    DropdownDynamicFieldConfiguration,
    DropdownDynamicSearchFieldConfiguration,
    UserDropdownFieldConfiguration,
]:
    WIDGET_ATTRIBUTES = WIDGET_ATTRIBUTES.union(WidgetType.__annotations__.keys())

COMPONENT_ATTRIBUTES: Set[str] = set()
for ComponentType in [
    SeparatorConfiguration,
    HtmlBlockConfiguration,
    RowConfiguration,
    PageConfiguration,
]:
    COMPONENT_ATTRIBUTES = COMPONENT_ATTRIBUTES.union(ComponentType.__annotations__.keys())
