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
        }
    ],
}
