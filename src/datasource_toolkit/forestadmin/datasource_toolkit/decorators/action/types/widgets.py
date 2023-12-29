from typing import List, Literal, Optional, Set, TypedDict

from typing_extensions import NotRequired


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


WIDGET_ATTRIBUTES: Set[str] = set()
for WidgetType in [
    ColorPickerFieldConfiguration,
    TextInputFieldConfiguration,
    TextAreaFieldConfiguration,
    RichTextFieldConfiguration,
    AddressAutocompleteFieldConfiguration,
    ArrayTextInputFieldConfiguration,
]:
    WIDGET_ATTRIBUTES = WIDGET_ATTRIBUTES.union(WidgetType.__annotations__.keys())
