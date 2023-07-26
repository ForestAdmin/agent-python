import io
import json
from operator import add, sub
from typing import List, Union

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.decorators.action.types.actions import ActionBulk, ActionSingle
from forestadmin.datasource_toolkit.decorators.action.types.fields import (
    PlainDynamicField,
    PlainFileListDynamicField,
    PlainListEnumDynamicField,
    PlainStringDynamicField,
)
from forestadmin.datasource_toolkit.decorators.chart.collection_chart_context import CollectionChartContext
from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder as ResultBuilderChart
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_customization_context import (
    WriteCustomizationContext,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionResult
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
        rows = await context.datasource.get_collection("order").aggregate(context.caller, condition, aggregation)
        # rows = await context.datasource.get_collection("order").aggregate(context.caller, condition, aggregation)
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
        column_type=PrimitiveType.STRING,
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


# actions
class ExportJson(ActionBulk):
    GENERATE_FILE: bool = True

    async def execute(self, context: ActionContextBulk, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        records = await context.get_records(Projection("id", "full name", "age"))
        return result_builder.file(
            io.BytesIO(json.dumps({"data": records}).encode("utf-8")),
            "dumps.json",
            "application/json",
        )


class AgeOperation(ActionSingle):
    @staticmethod
    def get_value_summary(context: ActionContextSingle):
        sentence = ""
        if context.form_values.get("Kind of operation", "") == "+":
            sentence += "add "
        elif context.form_values.get("Kind of operation", "") == "-":
            sentence += "minus "
        sentence += str(context.form_values.get("Value", ""))
        return sentence

    FORM: List[PlainDynamicField] = [
        {
            "type": ActionFieldType.ENUM,
            "label": "Kind of operation",
            "is_required": True,
            "default_value": "+",
            "value": "+",
            "enum_values": ["+", "-"],
        },
        {
            "type": ActionFieldType.NUMBER,
            "label": "Value",
            "default_value": 0,
        },
        {
            "type": ActionFieldType.STRING,
            "label": "summary",
            "is_required": False,
            "is_read_only": True,
            "value": get_value_summary,
        },
        PlainStringDynamicField(
            label="test list",
            type=ActionFieldType.STRING_LIST,
            # is_required=False,
            is_required=lambda context: context.form_values.get("Value", 11) > 10,
            is_read_only=lambda context: context.form_values.get("Value", 11) <= 10,
            if_=lambda context: context.form_values.get("Value", 11) > 10,
            # is_read_only=False,
            # default_value=[1, 2],
        ),
        PlainListEnumDynamicField(label="Rating", type=ActionFieldType.ENUM, enum_values=["1", "2", "3", "4", "5"]),
        PlainStringDynamicField(
            label="Put a comment",
            type=ActionFieldType.STRING,
            # Only display this field if the rating is 4 or 5
            if_=lambda context: int(context.form_values.get("Rating", "0") or "0") < 4,
        ),
        PlainFileListDynamicField(label="test filelist", type=ActionFieldType.FILE_LIST, is_required=False),
    ]

    async def execute(self, context: ActionContextSingle, result_builder: ResultBuilder) -> Union[None, ActionResult]:
        operation = add
        if context.form_values["Kind of operation"] == "-":
            operation = sub
        value = context.form_values["Value"]

        record = await context.get_record(Projection("age"))
        new_age = operation(record["age"], value)
        await context.collection.update(context.caller, context.filter, {"age": new_age})
        return result_builder.success("<h1> Success </h1>", options={"type": "html"})
        # return result_builder.success("Success")  # , options={"type": "html"})


# charts
async def total_orders_customer_chart(
    context: CollectionChartContext, result_builder: ResultBuilderChart, ids: CompositeIdAlias
):
    # total_spending = await context.get_record(Projection("TotalSpending"))
    orders = await context.datasource.get_collection("order").aggregate(
        caller=context.caller,
        filter=Filter({"condition_tree": ConditionTreeLeaf("customer_id", Operator.EQUAL, ids[0])}),
        # filter={"conditionTree": ConditionTreeLeaf("customer_id", Operator.EQUAL, ids[0])},
        aggregation=Aggregation({"field": "amount", "operation": "Sum"}),
    )
    # return result_builder.value(total_spending["TotalSpending"])
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
