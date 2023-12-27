from typing import List, Literal, TypedDict

from typing_extensions import NotRequired


class ColorPickerFieldConfiguration(TypedDict):
    widget: Literal["ColorPicker"]
    placeholder: NotRequired[str]
    enable_opacity: NotRequired[bool]
    quick_palette: NotRequired[List[str]]


_color_picker_attributes = set(["widget", "placeholder", "enable_opacity", "quick_palette"])


WIDGET_ATTRIBUTES = _color_picker_attributes
