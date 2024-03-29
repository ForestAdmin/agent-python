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
from forestadmin.datasource_toolkit.interfaces.actions import ActionResult
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias


# segments
def french_address_segment(context: CollectionCustomizationContext):
    return ConditionTreeLeaf(field="addresses:country", operator="equal", value="France")


# computed fields
def customer_spending_computed() -> ComputedDefinition:
    async def get_customer_spending_values(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        record_ids = [record["id"] for record in records]
        condition = Filter({"condition_tree": ConditionTreeLeaf(field="customer_id", operator="in", value=record_ids)})

        aggregation = Aggregation(
            {
                "operation": "Sum",
                "field": "amount",
                "groups": [{"field": "customer_id"}],
            }
        )
        rows = await context.datasource.get_collection("app_order").aggregate(context.caller, condition, aggregation)
        ret = []
        for record in records:
            filtered = [*filter(lambda r: r["group"]["customer_id"] == record["id"], rows)]
            row = filtered[0] if len(filtered) > 0 else {}
            ret.append(row.get("value", 0))

        return ret

    return {
        "column_type": "Number",
        "dependencies": ["id"],
        "get_values": get_customer_spending_values,
    }


def customer_full_name() -> ComputedDefinition:
    async def _get_customer_fullname_values(records: List[RecordsDataAlias], context: CollectionCustomizationContext):
        return [f"{record['first_name']} - {record['last_name']}" for record in records]

    return {
        "column_type": "String",
        "dependencies": ["first_name", "last_name"],
        "get_values": _get_customer_fullname_values,
    }


def customer_full_name_write(value: str, context: WriteCustomizationContext):
    first_name, last_name = value.split(" - ", 1)
    return {"first_name": first_name, "last_name": last_name}


# operator
async def full_name_equal(value, context: CollectionCustomizationContext) -> ConditionTree:
    first_name, last_name = value.split(" - ")
    return ConditionTreeBranch(
        "and",
        [
            ConditionTreeLeaf("first_name", "equal", first_name),
            ConditionTreeLeaf("last_name", "equal", last_name),
        ],
    )


async def full_name_less_than(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        "or",
        [
            ConditionTreeLeaf("first_name", "less_than", value),
            ConditionTreeBranch(
                "and",
                [
                    ConditionTreeLeaf("first_name", "equal", value),
                    ConditionTreeLeaf("last_name", "less_than", value),
                ],
            ),
        ],
    )


async def full_name_greater_than(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        "or",
        [
            ConditionTreeLeaf("first_name", "greater_than", value),
            ConditionTreeBranch(
                "and",
                [
                    ConditionTreeLeaf("first_name", "equal", value),
                    ConditionTreeLeaf("last_name", "greater_than", value),
                ],
            ),
        ],
    )


async def full_name_in(value, context: CollectionCustomizationContext):
    conditions = []
    for v in value:
        conditions.append(await full_name_equal(v, context))
    return ConditionTreeBranch("or", conditions)


async def full_name_not_in(value, context: CollectionCustomizationContext):
    condition_tree = await full_name_in(value, context)
    return condition_tree.inverse()


async def full_name_like(value, context: CollectionCustomizationContext):
    return ConditionTreeBranch(
        "or",
        [
            ConditionTreeLeaf("first_name", "like", value),
            ConditionTreeLeaf("last_name", "like", value),
        ],
    )


async def full_name_not_contains(value, context: CollectionCustomizationContext):
    if " - " in value:
        first_name, last_name = value.split(" - ")
        return ConditionTreeBranch(
            "and",
            [
                ConditionTreeLeaf("first_name", "not_contains", first_name),
                ConditionTreeLeaf("last_name", "not_contains", last_name),
            ],
        )
    else:
        return ConditionTreeBranch(
            "and",
            [
                ConditionTreeLeaf("first_name", "not_contains", value),
                ConditionTreeLeaf("last_name", "not_contains", value),
            ],
        )


async def full_name_contains(value, context: CollectionCustomizationContext):
    if " - " in value:
        first_name, last_name = value.split(" - ")
        return ConditionTreeBranch(
            "and",
            [
                ConditionTreeLeaf("first_name", "contains", first_name),
                ConditionTreeLeaf("last_name", "contains", last_name),
            ],
        )
    else:
        return ConditionTreeBranch(
            "and",
            [
                ConditionTreeLeaf("first_name", "contains", value),
                ConditionTreeLeaf("last_name", "contains", value),
            ],
        )


# actions
# ######## Export json


async def export_customers_json(context: ActionContextBulk, result_builder: ResultBuilder) -> ActionResult:
    records = await context.get_records(["id", "full_name", "age"])
    return result_builder.file(
        io.BytesIO(json.dumps({"data": records}).encode("utf-8")),
        "dumps.json",
        "application/json",
    )


export_json_action_dict: ActionDict = {
    "scope": "Bulk",
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
    "scope": "Single",
    "execute": age_operation_execute,
    "form": [
        {
            "type": "Enum",
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
            "type": "String",
            "label": "summary",
            "is_required": False,
            "is_read_only": True,
            "value": age_operation_get_value_summary,
        },
        {
            "label": "test list",
            "type": "StringList",
            "is_required": lambda context: context.form_values.get("Value", 11) > 10,
            "is_read_only": lambda context: context.form_values.get("Value", 11) <= 10,
            "if_": lambda context: context.form_values.get("Value", 0) > 10,
            "default_value": lambda context: ["1", "2"],
        },
        {"label": "Rating", "type": "Enum", "enum_values": ["1", "2", "3", "4", "5"]},
        {
            "label": "Put a comment",
            "type": "String",
            # Only display this field if the rating is 4 or 5
            "if_": lambda context: int(context.form_values.get("Rating", "0") or "0") < 4,
        },
        {"label": "test filelist", "type": "FileList", "is_required": False, "default_value": []},
    ],
}


# # charts
async def total_orders_customer_chart(
    context: CollectionChartContext, result_builder: ResultBuilderChart, ids: CompositeIdAlias
):
    orders = await context.datasource.get_collection("app_order").aggregate(
        caller=context.caller,
        filter_=Filter({"condition_tree": ConditionTreeLeaf("customer_id", "equal", ids[0])}),
        aggregation=Aggregation({"field": "amount", "operation": "Sum"}),
    )
    return result_builder.value(orders[0]["value"])


async def order_details(context: CollectionChartContext, result_builder: ResultBuilderChart, ids: CompositeIdAlias):
    orders = await context.datasource.get_collection("order").list(
        context.caller,
        PaginatedFilter(
            {"condition_tree": ConditionTreeLeaf("customer_id", "in", ids)},
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
