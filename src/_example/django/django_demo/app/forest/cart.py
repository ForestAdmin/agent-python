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


async def cart_get_customer_id(records, context):
    ret = []
    for rec in records:
        if rec.get("order") is not None:
            ret.append(rec["order"].get("customer_id"))
        else:
            ret.append(None)
    return ret
