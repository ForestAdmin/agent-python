from typing import Any, List

from aiohttp import ClientSession
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

# segments


async def high_delivery_address_segment(context: CollectionCustomizationContext):
    rows = await context.datasource.get_collection("app_order").aggregate(
        context.caller,
        Filter({}),
        Aggregation({"operation": "Count", "groups": [{"field": "delivering_address_id"}]}),
        100,
    )
    return ConditionTreeLeaf(field="id", operator="in", value=[row["group"]["delivering_address_id"] for row in rows])


# computed fields
def address_full_name_computed(country_field_name: str) -> ComputedDefinition:
    async def _get_full_address_values(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        ret = []
        for record in records:
            if record != {}:
                ret.append(f"{record.get('street')} {record.get('city')} {record.get(country_field_name)}")
            else:
                ret.append("")
        return ret

    return {
        "column_type": "String",
        "dependencies": ["street", country_field_name, "city"],
        "get_values": _get_full_address_values,
    }


def computed_full_address_caps():
    return {
        "column_type": "String",
        "dependencies": ["full address"],
        "get_values": lambda records, context: [record["full address"].upper() for record in records],
    }


async def get_postal_code(record: RecordsDataAlias, context: CollectionCustomizationContext) -> Any:
    async with ClientSession() as session:
        async with session.get(
            f"https://apicarto.ign.fr/api/codes-postaux/communes/{record.get('zip_code')}", verify_ssl=False
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                return []
