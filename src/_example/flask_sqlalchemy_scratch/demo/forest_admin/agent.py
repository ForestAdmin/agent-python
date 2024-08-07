from demo.forest_admin.forest_logging_customization import customize_forest_logging
from demo.forest_admin.smart.address import address_full_name_computed, get_postal_code, high_delivery_address_segment
from demo.forest_admin.smart.cart import cart_update_name
from demo.forest_admin.smart.customer import (
    age_operation_action_dict,
    customer_full_name,
    customer_full_name_write,
    customer_spending_computed,
    export_json_action_dict,
    french_address_segment,
    full_name_contains,
    full_name_equal,
    full_name_greater_than,
    full_name_in,
    full_name_less_than,
    full_name_like,
    full_name_not_contains,
    full_name_not_in,
    hook_customer_after_list,
    hook_customer_before_create,
    order_details,
    total_orders_customer_chart,
)
from demo.forest_admin.smart.order import (
    delivered_order_segment,
    dispatched_order_segment,
    export_orders_json,
    get_customer_full_name_field,
    nb_order_per_week,
    pending_order_segment,
    refund_order_action,
    rejected_order_segment,
    suspicious_order_segment,
    total_order_chart,
)
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.flask_agent.agent import FlaskAgent


def customize_agent(agent: FlaskAgent):
    customize_forest_logging()

    # # ## ADDRESS
    # segment
    agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment).rename_field(
        # fields
        "country",
        "pays",
    ).add_field("full_address", address_full_name_computed("country")).rename_field(
        "full_address", "complete_address"
    ).replace_field_sorting(
        "full_address",
        [
            {"field": "country", "ascending": True},
            {"field": "city", "ascending": True},
            {"field": "street", "ascending": True},
        ],
    ).remove_field(
        # changing visibility
        "street_number"
    ).disable_count(
        # deactivate count
    ).add_external_relation(
        # relation
        "postal_code",
        {
            "schema": {
                "codePostal": PrimitiveType.STRING,
                "codeCommune": PrimitiveType.STRING,
                "nomCommune": PrimitiveType.STRING,
                "libelleAcheminement": PrimitiveType.STRING,
            },
            "list_records": get_postal_code,
            "dependencies": ["zip_code"],
        },
    )

    # customers_addresses
    # smart relations
    agent.customize_collection("customers_addresses").add_many_to_one_relation(
        "smart_customers", "customer", "customer_id"
    ).add_many_to_one_relation("smart_addresses", "address", "address_id")

    # # ## CUSTOMERS
    # # import field ?
    # segments
    agent.customize_collection("customer").add_segment("with french address", french_address_segment).add_segment(
        "VIP customers", lambda context: ConditionTreeLeaf("is_vip", Operator.EQUAL, True)
    ).add_action(
        # actions
        "Export json",
        export_json_action_dict,
    ).add_action(
        # # action single with form
        "Age operation dict",
        age_operation_action_dict,
        # computed field
    ).add_field(
        "TotalSpending", customer_spending_computed()
    ).add_field(
        "full_name",
        customer_full_name(),
    ).replace_field_writing(
        # custom write on computed
        "full_name",
        customer_full_name_write,
        # custom operators for computed fields
    ).replace_field_operator(
        "full_name",
        Operator.EQUAL,
        full_name_equal,
    ).replace_field_operator(
        "full_name", Operator.IN, full_name_in
    ).replace_field_operator(
        "full_name", Operator.NOT_IN, full_name_not_in
    ).replace_field_operator(
        "full_name", Operator.LESS_THAN, full_name_less_than
    ).replace_field_operator(
        "full_name", Operator.GREATER_THAN, full_name_greater_than
    ).replace_field_operator(
        "full_name", Operator.LIKE, full_name_like
    ).replace_field_operator(
        "full_name", Operator.NOT_CONTAINS, full_name_not_contains
    ).replace_field_operator(
        "full_name", Operator.CONTAINS, full_name_contains
    ).emulate_field_filtering(
        "full_name"
        # validation
    ).add_field_validation(
        "age", Operator.GREATER_THAN, 0
    ).add_chart(
        # chart
        "total_orders",
        total_orders_customer_chart,
    ).add_chart(
        "orders_table", order_details
    ).add_many_to_many_relation(
        "smart_billing_addresses", "address", "order", "customer_id", "billing_address_id"
    ).add_many_to_many_relation(
        "smart_delivering_addresses", "address", "order", "customer_id", "delivering_address_id"
    )

    agent.customize_collection("cart").add_field(
        "customer_id",
        ComputedDefinition(
            column_type=PrimitiveType.UUID,
            dependencies=["order:customer_id"],
            get_values=lambda records, context: [rec["order"]["customer_id"] for rec in records],
        ),
    ).emulate_field_operator("customer_id", Operator.IN)
    agent.customize_collection("customer").add_one_to_many_relation("smart_carts", "cart", "customer_id").add_hook(
        # hooks
        "Before",
        "Create",
        hook_customer_before_create,
    ).add_hook("After", "List", hook_customer_after_list)

    # # ## ORDERS
    # # segment
    agent.customize_collection("order").add_segment("Pending order", pending_order_segment).add_segment(
        "Delivered order", delivered_order_segment
    ).add_segment("Rejected order", rejected_order_segment).add_segment(
        "Dispatched order", dispatched_order_segment
    ).add_segment(
        "Suspicious order", suspicious_order_segment
    ).add_segment(
        "newly_created",
        lambda context: ConditionTreeLeaf("created_at", Operator.AFTER, "2023-01-01"),
        # # rename
    ).rename_field(
        "amount",
        "cost",
        # # action file global
    ).add_action(
        "Export json", export_orders_json
    ).add_action(
        "Refund order(s)", refund_order_action
    ).add_field_validation(
        # # validation
        "amount",
        Operator.GREATER_THAN,
        0,
    ).add_field(
        # # computed
        "customer_full_name",
        get_customer_full_name_field(),
    ).import_field(
        "customer_first_name", {"path": "customer:first_name"}
    )

    # cart

    agent.customize_collection("cart").replace_field_writing("name", cart_update_name).add_segment(
        "No order", lambda ctx: ConditionTreeLeaf("order_id", Operator.EQUAL, None)
    )
    # general
    agent.add_chart("total_order", total_order_chart).add_chart(
        "mytablechart",
        lambda ctx, result_builder: result_builder.smart(
            [{"username": "Darth Vador", "points": 1500000}, {"username": "Luke Skywalker", "points": 2}]
        ),
    ).add_chart("total_order_week", nb_order_per_week)

    return agent
