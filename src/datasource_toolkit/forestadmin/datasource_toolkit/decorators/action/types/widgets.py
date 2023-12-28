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


WIDGET_ATTRIBUTES: Set[str] = set()
for WidgetType in [ColorPickerFieldConfiguration, TextInputFieldConfiguration]:
    WIDGET_ATTRIBUTES = WIDGET_ATTRIBUTES.union(WidgetType.__annotations__.keys())
