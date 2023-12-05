import io
import json
from typing import List, Union

from demo.models.models import ORDER_STATUS
from forestadmin.datasource_toolkit.context.agent_context import AgentCustomizationContext
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder as ResultBuilderChart
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionResult, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, DateOperation, PlainAggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from sqlalchemy.sql import text

# segments


def pending_order_segment(context: CollectionCustomizationContext):
    Session_ = context.collection.get_native_driver()
    with Session_() as connection:
        rows = connection.execute(text("select id, status from 'app_order' where status = 'PENDING'")).all()

    return ConditionTreeLeaf(
        field="id",
        operator=Operator.IN,
        value=[r[0] for r in rows],
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
async def execute_export_json(context: ActionContext, result_builder: ResultBuilder) -> Union[None, ActionResult]:
    records = await context.get_records(
        Projection(
            "id",
            "customer:full_name",
            "billing_address:full_address",
            "delivering_address:full_address",
            "status",
            "amount",
        )
    )
    return result_builder.file(
        io.BytesIO(json.dumps({"data": records}, default=str).encode("utf-8")), "dumps.json", "application/json"
    )


export_orders_json: ActionDict = {
    "scope": ActionsScope.GLOBAL,
    "generate_file": True,
    "execute": execute_export_json,
    "form": [
        {
            "type": ActionFieldType.STRING,
            "label": "dummy field",
            "is_required": False,
            "description": "",
            "default_value": "",
            "value": "",
        },
        {
            "type": ActionFieldType.COLLECTION,
            "collection_name": "app_customer",
            "label": "customer",
            "is_required": True,
            "description": "",
            "default_value": "",
            "value": "",
        },
    ],
}


async def refound_order_execute(context: ActionContext, result_builder: ResultBuilder) -> Union[None, ActionResult]:
    return result_builder.success("fake refund")


refound_order_action: ActionDict = {
    "scope": ActionsScope.BULK,
    "execute": refound_order_execute,
    "form": [
        {
            "type": ActionFieldType.STRING,
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
    records = await context.datasource.get_collection("order").list(
        context.caller, PaginatedFilter({}), Projection("id")
    )
    return result_builder.value(len(records))


async def nb_order_per_week(context: AgentCustomizationContext, result_builder: ResultBuilderChart):
    records = await context.datasource.get_collection("order").aggregate(
        context.caller,
        Filter({"condition_tree": ConditionTreeLeaf("created_at", Operator.BEFORE, "2022-01-01")}),
        Aggregation(
            PlainAggregation(
                field="created_at",
                operation="Count",
                groups=[{"field": "created_at", "operation": DateOperation.WEEK}],
            )
        ),
    )
    return result_builder.time_based(
        DateOperation.WEEK, {entry["group"]["created_at"]: entry["value"] for entry in records}
    )
