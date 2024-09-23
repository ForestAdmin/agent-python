import io
import json
from typing import List

from app.models import Order
from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder as ResultBuilderChart
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

# segments


def pending_order_segment(context: CollectionCustomizationContext):
    with context.collection.get_native_driver() as cursor:
        cursor.execute("select id, status from 'app_order' where status = 'PENDING'")
        rows = cursor.fetchall()

    return ConditionTreeLeaf(
        field="id",
        operator="in",
        value=[r[0] for r in rows],
        # value=[r[0] for r in rows[0 : min(len(rows), 32766)]],  # https://www.sqlite.org/c3ref/bind_blob.html
    )


def delivered_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator="equal",
        value=Order.OrderStatus.DELIVERED,
    )


def dispatched_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator="equal",
        value=Order.OrderStatus.DISPATCHED,
    )


def rejected_order_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(
        field="status",
        operator="equal",
        value=Order.OrderStatus.REJECTED,
    )


def suspicious_order_segment(context: CollectionCustomizationContext):
    too_old = ConditionTreeLeaf(field="customer:age", operator="greater_than", value=99)
    too_young = ConditionTreeLeaf(field="customer:age", operator="less_than", value=18)
    return ConditionTreeBranch("or", [too_old, too_young])


# computed fields
def get_customer_full_name_field() -> ComputedDefinition:
    async def get_customer_full_name_value(
        records: List[RecordsDataAlias], context: CollectionCustomizationContext
    ) -> List[str]:
        ret = []
        for record in records:
            if record.get("customer"):
                ret.append(f"{record['customer']['first_name']} {record['customer']['last_name']}")
            else:
                ret.append(None)
        return ret

    return {
        "column_type": "String",
        "dependencies": ["customer:first_name", "customer:last_name"],
        "get_values": get_customer_full_name_value,
    }


# actions
async def execute_export_json(context: ActionContext, result_builder: ResultBuilder) -> ActionResult:
    records = await context.get_records(
        [
            "id",
            "customer:full_name",
            "billing_address:full_address",
            "delivering_address:full_address",
            "status",
            "amount",
        ]
    )
    return result_builder.file(
        io.BytesIO(json.dumps({"data": records}, default=str).encode("utf-8")), "dumps.json", "application/json"
    )


export_orders_json: ActionDict = {
    "scope": "Global",
    "generate_file": True,
    "execute": execute_export_json,
    "form": [
        {
            "type": "String",
            "label": "dummy field",
            "is_required": False,
            "description": "",
            "default_value": "",
            "value": "",
        },
        {
            "type": "Layout",
            "component": "Separator",
            # "if_": lambda ctx: ctx.form_values.get("dummy field", "") == "aaa",
        },
        {
            "type": "Layout",
            "component": "HtmlBlock",
            "content": lambda ctx: "<b>A problem ?</b><a href='https://www.youtube.com/watch?v=dQw4w9WgXcQ' "
            "target='_blank'>This movie</a> can help you to fill this form !",
        },
        {
            "type": "Collection",
            "collection_name": "app_customer",
            "label": "customer",
            "is_required": True,
            "description": "",
            # "default_value": "",
            # "value": "",
        },
    ],
}


async def refund_order_execute(context: ActionContextSingle, result_builder: ResultBuilder) -> ActionResult:
    my_order_id = await context.get_record_id()
    my_order = await Order.objects.aget(id=my_order_id)
    # await my_order.refund()
    return result_builder.success(f"fake refund ({my_order.amount})")


refund_order_action: ActionDict = {
    "scope": "Single",
    "execute": refund_order_execute,
    "form": [
        {
            "type": "String",
            "label": "reason",
            "is_required": False,
            "description": "",
            "default_value": "",
            "value": "",
        },
    ],
}


# charts
async def total_order_chart(context: AgentCustomizationContext, result_builder: ResultBuilderChart):
    records = await context.datasource.get_collection("app_order").list(context.caller, PaginatedFilter({}), ["id"])
    return result_builder.value(len(records))


async def nb_order_per_week(context: AgentCustomizationContext, result_builder: ResultBuilderChart):
    records = await context.datasource.get_collection("app_order").aggregate(
        context.caller,
        Filter({"condition_tree": ConditionTreeLeaf("created_at", "before", "2022-01-01")}),
        Aggregation(
            {
                "field": "created_at",
                "operation": "Count",
                "groups": [{"field": "created_at", "operation": "Week"}],
            }
        ),
    )
    return result_builder.time_based("Week", {entry["group"]["created_at"]: entry["value"] for entry in records})
