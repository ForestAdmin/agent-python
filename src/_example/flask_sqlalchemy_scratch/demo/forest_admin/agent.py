from demo.forest_admin.forest_logging_customization import customize_forest_logging
from demo.forest_admin.settings import SETTINGS
from demo.forest_admin.smart.address import address_full_name_computed, get_postal_code, high_delivery_address_segment
from demo.forest_admin.smart.cart import cart_update_name
from demo.forest_admin.smart.customer import (
    AgeOperation,
    ExportJson,
    age_operation_action_dict,
    age_operation_action_obj_reuse,
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
from demo.forest_admin.smart.order import ExportJson as ExportOrderJson
from demo.forest_admin.smart.order import (
    RefundOrder,
    delivered_order_segment,
    dispatched_order_segment,
    export_orders_json,
    get_customer_full_name_field,
    nb_order_per_week,
    pending_order_segment,
    rejected_order_segment,
    suspicious_order_segment,
    total_order_chart,
)
from demo.models.models import SQLITE_URI, Base
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.flask_agent.agent import create_agent

agent = create_agent(SETTINGS)
agent.add_datasource(SqlAlchemyDatasource(Base, db_uri=SQLITE_URI))
customize_forest_logging()

# # ## ADDRESS
agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment)

agent.customize_collection("address").rename_field("country", "pays")
agent.customize_collection("address").add_field("full_address", address_full_name_computed("country"))
agent.customize_collection("address").rename_field("full_address", "complete_address")
agent.customize_collection("address").replace_field_sorting(
    "full_address",
    [
        {"field": "country", "ascending": True},
        {"field": "city", "ascending": True},
        {"field": "street", "ascending": True},
    ],
)

# customers_addresses
agent.customize_collection("customers_addresses").add_many_to_one_relation("smart_customers", "customer", "customer_id")
agent.customize_collection("customers_addresses").add_many_to_one_relation("smart_addresses", "address", "address_id")

# changing visibility
agent.customize_collection("address").remove_field("street_number")
# deactivate count
agent.customize_collection("address").disable_count()
agent.customize_collection("address").add_external_relation(
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

# # ## CUSTOMERS
# # import field ?
agent.customize_collection("customer").add_segment("with french address", french_address_segment)
# # action file bulk
agent.customize_collection("customer").add_segment(
    "VIP customers", lambda context: ConditionTreeLeaf("is_vip", Operator.EQUAL, True)
)

agent.customize_collection("customer").add_action("Export json class", ExportJson())
agent.customize_collection("customer").add_action("Export json dict", export_json_action_dict)
# # action single with form
agent.customize_collection("customer").add_action("Age operation class", AgeOperation())
agent.customize_collection("customer").add_action("Age operation manual class reuse", age_operation_action_obj_reuse)
agent.customize_collection("customer").add_action("Age operation dict", age_operation_action_dict)
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
agent.customize_collection("customer").replace_field_operator("full_name", Operator.CONTAINS, full_name_contains)
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
        column_type=PrimitiveType.BINARY,
        dependencies=["order:customer_id"],
        get_values=lambda records, context: [rec["order"]["customer_id"] for rec in records],
    ),
)
agent.customize_collection("cart").emulate_field_operator("customer_id", Operator.IN)
agent.customize_collection("customer").add_one_to_many_relation("smart_carts", "cart", "customer_id")

# hooks
agent.customize_collection("customer").add_hook("Before", "Create", hook_customer_before_create)
agent.customize_collection("customer").add_hook("After", "List", hook_customer_after_list)


# # ## ORDERS
# # segment
agent.customize_collection("order").add_segment("Pending order", pending_order_segment)
agent.customize_collection("order").add_segment("Delivered order", delivered_order_segment)
agent.customize_collection("order").add_segment("Rejected order", rejected_order_segment)
agent.customize_collection("order").add_segment("Dispatched order", dispatched_order_segment)
agent.customize_collection("order").add_segment("Suspicious order", suspicious_order_segment)
agent.customize_collection("order").add_segment(
    "newly_created", lambda context: ConditionTreeLeaf("created_at", Operator.AFTER, "2023-01-01")
)

# # rename
agent.customize_collection("order").rename_field("amount", "cost")
# # action file global
agent.customize_collection("order").add_action("Export json class", ExportOrderJson())
agent.customize_collection("order").add_action("Export json dict", export_orders_json)

agent.customize_collection("order").add_action("Refund order(s) class", RefundOrder())
agent.customize_collection("order").add_action("Refund order(s) call to_dict", RefundOrder().to_dict())
# # validation
agent.customize_collection("order").add_validation("amount", {"operator": Operator.GREATER_THAN, "value": 0})
# # computed
agent.customize_collection("order").add_field("customer_full_name", get_customer_full_name_field())

agent.customize_collection("order").import_field("customer_first_name", {"path": "customer:first_name"})

# cart

agent.customize_collection("cart").replace_field_writing("name", cart_update_name)
agent.customize_collection("cart").add_segment(
    "No order", lambda ctx: ConditionTreeLeaf("order_id", Operator.EQUAL, None)
)

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


# add charts
# # value
# # objective
# # percentage
# # distribution
# # leader-board
# # time-based

# hooks
# # before/after, write/read
