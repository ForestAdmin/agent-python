from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope


# field writing
async def cart_update_name(value, context: WriteCustomizationContext):
    s_val = value.split(" ")
    s_val.reverse()
    amount = None
    for word in s_val:
        try:
            amount = float(word) if "." in word else int(word)
            break
        except Exception:
            continue
    if amount is None:
        ret = {"name": value}
    else:
        ret = {"name": value, "order": {"amount": amount}}
    return ret


widget_action_form: ActionDict = {
    "scope": ActionsScope.GLOBAL,
    "execute": lambda context, result_builder: print("color: ", context.form_values.get("color")),
    "form": [
        {
            "label": "color",
            "type": ActionFieldType.STRING,
            "widget": "ColorPicker",
            "placeholder": "color",
            "enable_opacity": False,
            "quick_palette": [
                "#F7B13C",
                "#47B575",
            ],
        },
        {
            "label": "name",
            "type": ActionFieldType.STRING,
            "widget": "TextInput",
            "placeholder": "new_name",
        },
        {
            "label": "comment",
            "type": ActionFieldType.STRING,
            "widget": "TextArea",
            "placeholder": "long comment",
            "rows": 5,
        },
        {
            "label": "comment with style",
            "type": ActionFieldType.STRING,
            "widget": "RichText",
            "placeholder": "style comment",
        },
        {
            "label": "address",
            "type": ActionFieldType.STRING,
            "widget": "AddressAutocomplete",
            "placeholder": "where are you living ?",
        },
        {
            "label": "text list",
            "type": ActionFieldType.STRING_LIST,
            "widget": "TextInputList",
            "placeholder": "how many ??",
            "enable_reorder": False,
            "allow_duplicates": True,
        },
        {
            "label": "number",
            "type": ActionFieldType.NUMBER,
            "widget": "NumberInput",
            "placeholder": "???",
        },
        {
            "label": "numbers",
            "type": ActionFieldType.NUMBER_LIST,
            "widget": "NumberInputList",
            "placeholder": "???",
            "min": -1,
            "max": 10,
            "step": 0.5,
            "allow_duplicates": True,
        },
        {
            "label": "json ",
            "type": ActionFieldType.JSON,
            "widget": "JsonEditor",
        },
        {
            "label": "Price",
            "type": ActionFieldType.NUMBER,
            "widget": "CurrencyInput",
            "min": 0,
            "max": 100,
            "currency": "usd",
        },
        {
            "label": "file list",
            "type": ActionFieldType.FILE_LIST,
            "widget": "FilePicker",
            "max_size_mb": 10,
            "max_count": 1,
            "extensions": ["png"],
        },
    ],
}
