from typing import List, Tuple

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    Aggregation,
    PlainAggregation,
    PlainAggregationGroup,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

# segments


async def high_delivery_address_segment(context: CollectionCustomizationContext):
    rows = await context.datasource.get_collection("order").aggregate(
        None,
        Aggregation(
            component=PlainAggregation(
                PlainAggregation(operation="Count", groups=[PlainAggregationGroup(field="delivering_address_id")])
            )
        ),
        100,
    )
    return ConditionTreeLeaf(
        field="id", operator=Operator.IN, value=[row["group"]["delivering_address_id"] for row in rows]
    )


# computed fields
def address_full_name_computed(country_field_name: str) -> Tuple[str, ComputedDefinition]:
    async def _get_full_address_values(records: List[RecordsDataAlias], _: CollectionCustomizationContext):
        return [f"{record['street']} {record['city']} {record[country_field_name]}" for record in records]

    return ComputedDefinition(
        column_type=PrimitiveType.STRING,
        dependencies=["street", country_field_name, "city"],
        get_values=_get_full_address_values,
    )
    # or {
    #     "column_type": PrimitiveType.STRING,
    #     "dependencies": ["street", country_field_name, "city"],
    #     "get_values": _get_full_address_values,
    # },


def computed_full_address_caps():
    return ComputedDefinition(
        column_type=PrimitiveType.STRING,
        dependencies=["full address"],
        get_values=lambda records, context: [record["full address"].upper() for record in records],
    )
