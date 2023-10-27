from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)


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
