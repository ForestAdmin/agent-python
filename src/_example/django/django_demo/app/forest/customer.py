import io
import json
import logging
from operator import add, sub
from typing import List

from dateutil.relativedelta import relativedelta
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionDict
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder as ResultBuilderChart
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.hook.context.create import HookBeforeCreateContext
from forestadmin.datasource_toolkit.decorators.hook.context.list import HookAfterListContext
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionResult, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    Aggregation,
    PlainAggregation,
    PlainAggregationGroup,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias


# segments
def french_address_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(field="addresses:country", operator=Operator.EQUAL, value="France")


# computed fields
def customer_spending_computed():
    async def get_customer_spending_values(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        record_ids = [record["id"] for record in records]
        condition = Filter(
            {"condition_tree": ConditionTreeLeaf(field="customer_id", operator=Operator.IN, value=record_ids)}
        )

        aggregation = Aggregation(
            component=PlainAggregation(
                operation="Sum",
                field="amount",
                groups=[PlainAggregationGroup(field="customer_id")],
            ),
        )
        rows = await context.datasource.get_collection("app_order").aggregate(context.caller, condition, aggregation)
        ret = []
        for record in records:
            filtered = [*filter(lambda r: r["group"]["customer_id"] == record["id"], rows)]
            row = filtered[0] if len(filtered) > 0 else {}
            ret.append(row.get("value", 0))

        return ret

    return ComputedDefinition(
        column_type=PrimitiveType.NUMBER, dependencies=["id"], get_values=get_customer_spending_values
    )


def customer_full_name() -> ComputedDefinition:
    async def _get_customer_fullname_values(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        return [f"{record['first_name']} - {record['last_name']}" for record in records]

    return ComputedDefinition(
        column_type="String",
        dependencies=["first_name", "last_name"],
        get_values=_get_customer_fullname_values,
    )
    # or
    # return {
    #     "column_type": PrimitiveType.STRING,
    #     "dependencies": ["first_name", "last_name"],
    #     "get_values": _get_customer_fullname_values,
    # }


def customer_full_name_write(value: str, context: WriteCustomizationContext):
    first_name, last_name = value.split(" - ", 1)
    return {"first_name": first_name, "last_name": last_name}


# operator
async def full_name_equal(value, context: CollectionCustomizationContext) -> ConditionTree:
    first_name, last_name = value.split(" - ")
    return ConditionTreeBranch(
        Aggregator.AND,
        [
            ConditionTreeLeaf("first_name", Operator.EQUAL, first_name),
            ConditionTreeLeaf("last_name", Operator.EQUAL, last_name),
        ],
    )


async def full_name_less_than(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        Aggregator.OR,
        [
            ConditionTreeLeaf("first_name", Operator.LESS_THAN, value),
            ConditionTreeBranch(
                Aggregator.AND,
                [
                    ConditionTreeLeaf("first_name", Operator.EQUAL, value),
                    ConditionTreeLeaf("last_name", Operator.LESS_THAN, value),
                ],
            ),
        ],
    )


async def full_name_greater_than(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        Aggregator.OR,
        [
            ConditionTreeLeaf("first_name", Operator.GREATER_THAN, value),
            ConditionTreeBranch(
                Aggregator.AND,
                [
                    ConditionTreeLeaf("first_name", Operator.EQUAL, value),
                    ConditionTreeLeaf("last_name", Operator.GREATER_THAN, value),
                ],
            ),
        ],
    )


async def full_name_in(value, context: CollectionCustomizationContext):
    conditions = []
    for v in value:
        conditions.append(await full_name_equal(v, context))
    return ConditionTreeBranch(Aggregator.OR, conditions)


async def full_name_not_in(value, context: CollectionCustomizationContext):
    condition_tree = await full_name_in(value, context)
    return condition_tree.inverse()


async def full_name_like(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        Aggregator.OR,
        [
            ConditionTreeLeaf("first_name", Operator.LIKE, value),
            ConditionTreeLeaf("last_name", Operator.LIKE, value),
        ],
    )


async def full_name_not_contains(value, context: CollectionCustomizationContext):
    if " - " in value:
        first_name, last_name = value.split(" - ")
        return ConditionTreeBranch(
            Aggregator.AND,
            [
                ConditionTreeLeaf("first_name", Operator.NOT_CONTAINS, first_name),
                ConditionTreeLeaf("last_name", Operator.NOT_CONTAINS, last_name),
            ],
        )
    else:
        return ConditionTreeBranch(
            Aggregator.AND,
            [
                ConditionTreeLeaf("first_name", Operator.NOT_CONTAINS, value),
                ConditionTreeLeaf("last_name", Operator.NOT_CONTAINS, value),
            ],
        )


async def full_name_contains(value, context: CollectionCustomizationContext):
    if " - " in value:
        first_name, last_name = value.split(" - ")
        return ConditionTreeBranch(
            Aggregator.AND,
            [
                ConditionTreeLeaf("first_name", Operator.CONTAINS, first_name),
                ConditionTreeLeaf("last_name", Operator.CONTAINS, last_name),
            ],
        )
    else:
        return ConditionTreeBranch(
            Aggregator.AND,
            [
                ConditionTreeLeaf("first_name", Operator.CONTAINS, value),
                ConditionTreeLeaf("last_name", Operator.CONTAINS, value),
            ],
        )


# actions
# ######## Export json


async def export_customers_json(context: ActionContextBulk, result_builder: ResultBuilder) -> ActionResult:
    records = await context.get_records(Projection("id", "full name", "age"))
    return result_builder.file(
        io.BytesIO(json.dumps({"data": records}).encode("utf-8")),
        "dumps.json",
        "application/json",
    )


export_json_action_dict: ActionDict = {
    "scope": "bulk",
    "generate_file": True,
    "execute": export_customers_json,
}


# ######## Age Operation


# dict style
def age_operation_get_value_summary(context: ActionContextSingle) -> str:
    if not context.has_field_changed("Kind of operation") and not context.has_field_changed("Value"):
        return context.form_values.get("summary")
    sentence: str = "add " if context.form_values.get("Kind of operation", "") == "+" else "minus "
    sentence += str(context.form_values.get("Value", ""))
    return sentence


async def age_operation_execute(context: ActionContextSingle, result_builder: ResultBuilder) -> ActionResult:
    operation = add
    if context.form_values["Kind of operation"] == "-":
        operation = sub
    value = context.form_values["Value"]

    record = await context.get_record(Projection("birthday_date"))
    new_birthday = operation(record["birthday_date"], relativedelta(years=value))
    await context.collection.update(context.caller, context.filter, {"birthday_date": new_birthday})

    return result_builder.set_header("MyCustomHeader", "MyCustomValue").success(
        "<h1> Success </h1>", options={"type": "html"}
    )


age_operation_action_dict: ActionDict = {
    "scope": ActionsScope.SINGLE,
    "execute": age_operation_execute,
    "form": [
        {
            "type": ActionFieldType.ENUM,
            "label": "Kind of operation",
            "is_required": True,
            "default_value": "+",
            "value": "+",
            "enum_values": ["+", "-"],
        },
        {
            "type": "Number",
            "label": "Value",
            "default_value": 0,
        },
        {
            "type": ActionFieldType.STRING,
            "label": "summary",
            "is_required": False,
            "is_read_only": True,
            "value": age_operation_get_value_summary,
        },
        {
            "label": "test list",
            "type": ActionFieldType.STRING_LIST,
            "is_required": lambda context: context.form_values.get("Value", 11) > 10,
            "is_read_only": lambda context: context.form_values.get("Value", 11) <= 10,
            "if_": lambda context: context.form_values.get("Value", 0) > 10,
            "default_value": lambda context: ["1", "2"],
        },
        {"label": "Rating", "type": ActionFieldType.ENUM, "enum_values": ["1", "2", "3", "4", "5"]},
        {
            "label": "Put a comment",
            "type": ActionFieldType.STRING,
            # Only display this field if the rating is 4 or 5
            "if_": lambda context: int(context.form_values.get("Rating", "0") or "0") < 4,
        },
        {"label": "test filelist", "type": ActionFieldType.FILE_LIST, "is_required": False, "default_value": []},
    ],
}


# # charts
async def total_orders_customer_chart(
    context: CollectionChartContext, result_builder: ResultBuilderChart, ids: CompositeIdAlias
):
    orders = await context.datasource.get_collection("order").aggregate(
        caller=context.caller,
        filter_=Filter({"condition_tree": ConditionTreeLeaf("customer_id", Operator.EQUAL, ids[0])}),
        aggregation=Aggregation({"field": "amount", "operation": "Sum"}),
    )
    return result_builder.value(orders[0]["value"])


async def order_details(context: CollectionChartContext, result_builder: ResultBuilderChart, ids: CompositeIdAlias):
    orders = await context.datasource.get_collection("order").list(
        context.caller,
        PaginatedFilter(
            {"condition_tree": ConditionTreeLeaf("customer_id", Operator.IN, ids)},
        ),
        Projection("id", "customer_full_name"),
    )
    return result_builder.smart(orders)


#  hooks


def hook_customer_before_create(context: HookBeforeCreateContext):
    for data in context.data:
        if data.get("last_name", "").lower() == "norris" and data.get("first_name", "").lower() == "chuck":
            context.throw_forbidden_error("You can't hit Chuck Norris; even on a keyboard !!!")


async def hook_customer_after_list(context: HookAfterListContext):
    logger = logging.getLogger("forestadmin")
    if context.filter.condition_tree is not None:
        logger.info("you're looking for someone ??")

    if len(context.records) > 0:
        logger.info("All these customers, you must be rich !!!")
    else:
        logger.info("No customers, No problems !!!")
