import io
import json
from typing import List, Union

from demo.models.models import ORDER_STATUS
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionGlobal
from forestadmin.datasource_toolkit.decorators.action.types.fields import PlainDynamicField
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionResult
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

# segments


def pending_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator=Operator.EQUAL,
        value=ORDER_STATUS.PENDING,
    )


def delivered_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator=Operator.EQUAL,
        value=ORDER_STATUS.DELIVERED,
    )


def dispatched_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator=Operator.EQUAL,
        value=ORDER_STATUS.DISPATCHED,
    )


def rejected_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator=Operator.EQUAL,
        value=ORDER_STATUS.REJECTED,
    )


def suspicious_order_segment(context: CollectionCustomizationContext):
    too_old = ConditionTreeLeaf(field="customer:age", operator=Operator.GREATER_THAN, value=99)
    too_young = ConditionTreeLeaf(field="customer:age", operator=Operator.LESS_THAN, value=18)
    return ConditionTreeBranch(Aggregator.OR, [too_old, too_young])


# computed fields
def get_customer_full_name_field():
    async def get_customer_full_name_value(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        return [f"{record['customer']['first_name']} {record['customer']['last_name']}" for record in records]

    return ComputedDefinition(
        column_type=PrimitiveType.STRING,
        dependencies=["customer:first_name", "customer:last_name"],
        get_values=get_customer_full_name_value,
    )


# actions
class ExportJson(ActionGlobal):
    GENERATE_FILE: bool = True
    FORM: List[PlainDynamicField] = [
        {
            "type": ActionFieldType.STRING,
            "label": "dummy field",
            "is_required": False,
            "description": "",
            "default_value": "",
            "value": "",
        },
    ]

    async def execute(self, context: ActionContext, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        records = await context.get_records(
            Projection(
                "id",
                "customer:full name",
                "billing_address:complete_address",
                "delivering_address:complete_address",
                "status",
                # "amount",
                "cost",
            )
        )
        return result_builder.file(
            io.BytesIO(json.dumps({"data": records}, default=str).encode("utf-8")), "dumps.json", "application/json"
        )
