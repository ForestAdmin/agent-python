from typing import Awaitable, Callable, List, Literal, Optional, Set, TypedDict, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from typing_extensions import NotRequired

Number = Union[int, float]

Context = TypeVar("Context", bound=ActionContext)
Result = TypeVar("Result")

ValueOrHandler = Union[Callable[[Context], Awaitable[Result]], Callable[[Context], Result], Result]


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
    widget: Literal["TextArea"]
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
]:
    WIDGET_ATTRIBUTES = WIDGET_ATTRIBUTES.union(WidgetType.__annotations__.keys())
