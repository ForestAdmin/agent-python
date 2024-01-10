from datetime import date
from typing import Awaitable, Callable, Generic, List, Literal, Optional, Set, TypedDict, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from typing_extensions import NotRequired

Number = Union[int, float]

Context = TypeVar("Context", bound=ActionContext)
Result = TypeVar("Result")

TWidget = TypeVar("TWidget")
TValue = TypeVar("TValue")

ValueOrHandler = Union[Callable[[Context], Union[Awaitable[Result], Result]], Result]


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
    min: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    max: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    step: NotRequired[Optional[ValueOrHandler[Context, Number]]]


class NumberInputListFieldConfiguration(TypedDict):
    widget: Literal["NumberInputList"]
    min: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    max: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    step: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    placeholder: NotRequired[Optional[str]]
    enable_reorder: NotRequired[Optional[bool]]
    allow_empty_values: NotRequired[Optional[bool]]
    allow_duplicates: NotRequired[Optional[bool]]


class CurrencyInputFieldConfiguration(TypedDict):
    widget: Literal["CurrencyInput"]
    placeholder: NotRequired[Optional[str]]
    currency: NotRequired[Optional[str]]
    base: NotRequired[Optional[ValueOrHandler[Context, Literal["Unit", "Cent"]]]]
    min: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    max: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    step: NotRequired[Optional[ValueOrHandler[Context, Number]]]


class JsonEditorFieldConfiguration(TypedDict):
    widget: Literal["JsonEditor"]


class FilePickerFieldConfiguration(TypedDict):
    widget: Literal["FilePicker"]
    extensions: NotRequired[Optional[ValueOrHandler[Context, List[str]]]]
    max_size_mb: NotRequired[Optional[ValueOrHandler[Context, Number]]]


class FileListPickerFieldConfiguration(TypedDict):
    widget: Literal["FilePicker"]
    extensions: NotRequired[Optional[ValueOrHandler[Context, List[str]]]]
    max_size_mb: NotRequired[Optional[ValueOrHandler[Context, Number]]]
    max_count: NotRequired[Optional[ValueOrHandler[Context, Number]]]


class TimePickerFieldConfiguration(TypedDict):
    widget: Literal["TimePicker"]


class DatePickerFieldConfiguration(TypedDict):
    widget: Literal["DatePicker"]
    placeholder: NotRequired[Optional[str]]
    format: NotRequired[Optional[ValueOrHandler[Context, str]]]
    min: NotRequired[Optional[ValueOrHandler[Context, date]]]
    max: NotRequired[Optional[ValueOrHandler[Context, date]]]


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
    options: Union[List[DropdownOption], Callable[[Context], List[DropdownOption]], Awaitable[List[DropdownOption]]]


class RadioButtonFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["RadioGroup"], TValue]):
    pass


class CheckboxesFieldConfiguration(LimitedValueDynamicFieldConfiguration[Literal["CheckboxGroup"], TValue]):
    pass


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
]:
    WIDGET_ATTRIBUTES = WIDGET_ATTRIBUTES.union(WidgetType.__annotations__.keys())
