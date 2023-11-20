from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter


async def get_customer_spent_values(records, context: CollectionCustomizationContext):
    record_ids = [record["id"] for record in records]
    condition = Filter(
        {"condition_tree": ConditionTreeLeaf(field="customer_id", operator=Operator.IN, value=record_ids)}
    )

    aggregation = Aggregation(
        {
            "operation": "Sum",
            "field": "amount",
            "groups": [
                {
                    "field": "customer_id",
                }
            ],
        },
    )
    rows = await context.datasource.get_collection("Order").aggregate(context.caller, condition, aggregation)
    # rows = await context.datasource.get_collection("order").aggregate(context.caller, condition, aggregation)
    ret = []
    for record in records:
        filtered = [*filter(lambda r: r["group"]["customer_id"] == record["id"], rows)]
        row = filtered[0] if len(filtered) > 0 else {}
        ret.append(row.get("value", 0))

    return ret
