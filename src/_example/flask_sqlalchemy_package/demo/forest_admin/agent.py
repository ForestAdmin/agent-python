from demo.forest_admin.forest_logging_customization import customize_forest_logging
from demo.forest_admin.smart.address import address_full_name_computed, high_delivery_address_segment
from demo.forest_admin.smart.cart import cart_update_name
from demo.forest_admin.smart.customer import (
    AgeOperation,
    ExportJson,
    customer_full_name,
    customer_full_name_write,
    customer_spending_computed,
    french_address_segment,
    full_name_equal,
    full_name_greater_than,
    full_name_in,
    full_name_less_than,
    full_name_like,
    full_name_not_contains,
    full_name_not_in,
    order_details,
    total_orders_customer_chart,
)
from demo.forest_admin.smart.order import ExportJson as ExportOrderJson
from demo.forest_admin.smart.order import (
    delivered_order_segment,
    dispatched_order_segment,
    get_customer_full_name_field,
    nb_order_per_week,
    pending_order_segment,
    rejected_order_segment,
    suspicious_order_segment,
    total_order_chart,
)
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.flask_agent.agent import Agent


def customize_agent(agent: Agent):
    customize_forest_logging()

    # # ## ADDRESS
    agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment)

    agent.customize_collection("address").rename_field("country", "pays")
    agent.customize_collection("address").add_field("full_address", address_full_name_computed("country"))
    agent.customize_collection("address").rename_field("full_address", "complete_address")

    # changing visibility
    agent.customize_collection("address").remove_field("zip_code")
    # deactivate count
    agent.customize_collection("address").disable_count()

    # customers_addresses
    agent.customize_collection("customers_addresses").add_many_to_one_relation(
        "smart_customers", "customer", "customer_id"
    )
    agent.customize_collection("customers_addresses").add_many_to_one_relation(
        "smart_addresses", "address", "address_id"
    )

    # # ## CUSTOMERS
    # # import field ?
    agent.customize_collection("customer").add_segment("with french address", french_address_segment)
    agent.customize_collection("customer").add_segment(
        "VIP customers", lambda context: ConditionTreeLeaf("is_vip", Operator.EQUAL, True)
    )
    # # action file bulk
    agent.customize_collection("customer").add_action("Export json", ExportJson())
    # # action single with form
    agent.customize_collection("customer").add_action("Age operation", AgeOperation())
    # # computed
    agent.customize_collection("customer").add_field("full_name", customer_full_name())
    # custom write on computed
    agent.customize_collection("customer").replace_field_writing("full_name", customer_full_name_write)

    # custom operators for computed fields
    agent.customize_collection("customer").replace_field_operator("full_name", Operator.EQUAL, full_name_equal)
    agent.customize_collection("customer").replace_field_operator("full_name", Operator.IN, full_name_in)
    agent.customize_collection("customer").replace_field_operator("full_name", Operator.NOT_IN, full_name_not_in)
    agent.customize_collection("customer").replace_field_operator("full_name", Operator.LESS_THAN, full_name_less_than)
    agent.customize_collection("customer").replace_field_operator(
        "full_name", Operator.GREATER_THAN, full_name_greater_than
    )
    agent.customize_collection("customer").replace_field_operator("full_name", Operator.LIKE, full_name_like)
    agent.customize_collection("customer").replace_field_operator(
        "full_name", Operator.NOT_CONTAINS, full_name_not_contains
    )
    # emulate others operators
    agent.customize_collection("customer").emulate_field_filtering("full_name")

    agent.customize_collection("customer").add_field("TotalSpending", customer_spending_computed())
    # # validation
    agent.customize_collection("customer").add_validation("age", {"operator": Operator.GREATER_THAN, "value": 0})
    agent.customize_collection("customer").add_chart("total_orders", total_orders_customer_chart)
    agent.customize_collection("customer").add_chart("orders_table", order_details)
    agent.customize_collection("customer").add_many_to_many_relation(
        "smart_billing_addresses", "address", "order", "customer_id", "billing_address_id"
    )
    agent.customize_collection("customer").add_many_to_many_relation(
        "smart_delivering_addresses", "address", "order", "customer_id", "delivering_address_id"
    )

    agent.customize_collection("cart").add_field(
        "customer_id",
        ComputedDefinition(
            column_type=PrimitiveType.NUMBER,
            dependencies=["order:customer_id"],
            get_values=lambda records, context: [rec["order"]["customer_id"] for rec in records],
        ),
    )
    agent.customize_collection("cart").emulate_field_operator("customer_id", Operator.IN)
    agent.customize_collection("customer").add_one_to_many_relation("smart_carts", "cart", "customer_id")

    # # ## ORDERS
    # # segment
    agent.customize_collection("order").add_segment("Pending order", pending_order_segment)
    agent.customize_collection("order").add_segment("Delivered order", delivered_order_segment)
    agent.customize_collection("order").add_segment("Rejected order", rejected_order_segment)
    agent.customize_collection("order").add_segment("Dispatched order", dispatched_order_segment)
    agent.customize_collection("order").add_segment("Suspicious order", suspicious_order_segment)

    # # rename
    agent.customize_collection("order").rename_field("amount", "cost")
    # # action file global
    agent.customize_collection("order").add_action("Export json", ExportOrderJson())
    # # validation
    agent.customize_collection("order").add_validation("amount", {"operator": Operator.GREATER_THAN, "value": 0})
    # # computed
    agent.customize_collection("order").add_field("customer_full_name", get_customer_full_name_field())

    # cart
    agent.customize_collection("cart").replace_field_writing("name", cart_update_name)

    agent.add_chart("total_order", total_order_chart)
    agent.add_chart(
        "mytablechart",
        lambda ctx, result_builder: result_builder.smart(
            [{"username": "Darth Vador", "points": 1500000}, {"username": "Luke Skywalker", "points": 2}]
        ),
    )
    agent.add_chart("total_order_week", nb_order_per_week)

    # add relations
    # # oneToOne
    # # externalRelation

    # hooks
    # # before/after, write/read
