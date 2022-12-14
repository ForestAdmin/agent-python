from typing import Any, List, Tuple

from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def address_full_name() -> Tuple[str, ComputedDefinition]:
    async def _get_values(records: List[RecordsDataAlias], _: Any):
        return [f"{record['street']} {record['city']} {record['country']}" for record in records]

    return (
        "full address",
        {"column_type": PrimitiveType.STRING, "dependencies": ["street", "country", "city"], "get_values": _get_values},
    )
