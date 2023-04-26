from typing import Any, List, Tuple

from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


# field = "pays"
field = "country"


def address_full_name() -> Tuple[str, ComputedDefinition]:
    async def _get_values(records: List[RecordsDataAlias], _: Any):
        return [f"{record['street']} {record['city']} {record[field]}" for record in records]

    return (
        "full address",
        {"column_type": PrimitiveType.STRING, "dependencies": ["street", field, "city"], "get_values": _get_values},
    )
