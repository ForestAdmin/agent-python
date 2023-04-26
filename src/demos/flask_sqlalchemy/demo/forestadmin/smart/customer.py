import io
import json
from operator import add, sub
from typing import Any, List, Tuple, Union

from forestadmin.datasource_toolkit.context.collection_context import (
    CollectionCustomizationContext,
)
from forestadmin.datasource_toolkit.decorators.action.context.bulk import (
    ActionContextBulk,
)
from forestadmin.datasource_toolkit.decorators.action.context.single import (
    ActionContextSingle,
)
from forestadmin.datasource_toolkit.decorators.action.result_builder import (
    ResultBuilder,
)
from forestadmin.datasource_toolkit.decorators.action.types.actions import (
    ActionBulk,
    ActionSingle,
)
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainDynamicField,
)
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionFieldType,
    ActionResult,
)
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def customer_full_name() -> Tuple[str, ComputedDefinition]:
    async def _get_values(records: List[RecordsDataAlias], _: Any):
        return [f"{record['first_name']} {record['last_name']}" for record in records]

    return (
        "full name",
        {
            "column_type": PrimitiveType.STRING,
            "dependencies": ["first_name", "last_name"],
            "get_values": _get_values,
        },
    )


def french_address_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(field="addresses:country", operator=Operator.EQUAL, value="France")


class ExportJson(ActionBulk):
    GENERATE_FILE: bool = True

    async def execute(self, context: ActionContextBulk, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        records = await context.get_records(Projection("id", "full name", "age"))
        return result_builder.file(
            io.BytesIO(json.dumps({"data": records}).encode("utf-8")),
            "dumps.json",
            "application/json",
        )


async def get_value_summary(context: ActionContextSingle, *args, **kwargs):
    sentence = ""
    if context.form_values.get("Kind of operation", "") == "+":
        sentence += "add "
    elif context.form_values.get("Kind of operation", "") == "-":
        sentence += "minus "
    sentence += str(context.form_values.get("Value", ""))
    return sentence


class AgeOperation(ActionSingle):
    FORM: List[PlainDynamicField] = [
        {
            "type": ActionFieldType.ENUM,
            "label": "Kind of operation",
            "is_required": True,
            "description": "",
            "default_value": "+",
            "value": "+",
            "enum_values": ["+", "-"],
        },
        {
            "type": ActionFieldType.NUMBER,
            "label": "Value",
            "description": "",
            "default_value": 0,
        },
        {
            "type": ActionFieldType.STRING,
            "label": "summary",
            "description": "",
            "is_required": False,
            "is_read_only": True,
            "value": get_value_summary,
        },
        {
            "type": ActionFieldType.NUMBER_LIST,
            "label": "test list",
            "description": "",
            "is_required": False,
            "is_read_only": False,
            "default_value": [1, 2],
        },
    ]

    async def execute(self, context: ActionContextSingle, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        operation = add
        if context.form_values["Kind of operation"] == "-":
            operation = sub
        value = context.form_values["Value"]

        record = await context.get_record(Projection("age"))
        new_age = operation(record["age"], value)
        await context.collection.update(context.filter, {"age": new_age})
        return result_builder.success("<h1> Success </h1>", options={"type": "html"})
