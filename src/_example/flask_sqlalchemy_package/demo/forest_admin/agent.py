from demo.forest_admin.smart.address import address_full_name_computed, high_delivery_address_segment
from demo.forest_admin.smart.customer import (
    AgeOperation,
    ExportJson,
    customer_full_name,
    customer_spending_computed,
    french_address_segment,
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
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.flask_agent.agent import Agent


def customize_agent(agent: Agent):
    # # ## ADDRESS
    agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment)

    # agent.customize_collection("address").rename_field("country", "pays")
    agent.customize_collection("address").add_field("full_address", address_full_name_computed("country"))
    agent.customize_collection("address").rename_field("full_address", "complete_address")

    # changing visibility
    agent.customize_collection("address").remove_field("zip_code")
    # deactivate count
    agent.customize_collection("address").disable_count()

    # # ## CUSTOMERS
    # # import field ?
    agent.customize_collection("customer").add_segment("with french address", french_address_segment)
    # # action file bulk
    agent.customize_collection("customer").add_action("Export json", ExportJson())
    # # action single with form
    agent.customize_collection("customer").add_action("Age operation", AgeOperation())
    # # computed
    agent.customize_collection("customer").add_field("full_name", customer_full_name())
    agent.customize_collection("customer").add_field("TotalSpending", customer_spending_computed())
    # # validation
    agent.customize_collection("customer").add_validation("age", {"operator": Operator.GREATER_THAN, "value": 0})
    agent.customize_collection("customer").add_chart("total_orders", total_orders_customer_chart)
    agent.customize_collection("customer").add_chart("orders_table", order_details)

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

    agent.add_chart("total_order", total_order_chart)
    agent.add_chart(
        "mytablechart",
        lambda ctx, result_builder: result_builder.smart(
            [{"username": "Darth Vador", "points": 1500000}, {"username": "Luke Skywalker", "points": 2}]
        ),
    )
    agent.add_chart("total_order_week", nb_order_per_week)

    # add relations
    # # manyToOne
    # # oneToOne
    # # oneToMany
    # # ManyToMany
    # # externalRelation

    # add charts
    # # value
    # # objective
    # # percentage
    # # distribution
    # # leader-board
    # # time-based

    # hooks
    # # before/after, write/read
