import datetime

from app.forest.address import (
    address_full_name_computed,
    get_postal_code,
    high_delivery_address_segment,
    segment_addr_fr,
)
from app.forest.cart import cart_get_customer_id, cart_update_name
from app.forest.custom_datasources.typicode import TypicodeDatasource
from app.forest.customer import (
    age_operation_action_dict,
    customer_delete_override,
    customer_full_name,
    customer_full_name_write,
    customer_spending_computed,
    customer_update_override,
    export_json_action_dict,
    french_address_segment,
    full_name_contains,
    full_name_equal,
    full_name_in,
    full_name_like,
    full_name_not_contains,
    full_name_not_in,
    hook_customer_after_list,
    hook_customer_before_create,
    order_details,
    time_order_number_chart,
    total_orders_customer_chart,
)
from app.forest.order import (
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
from app.sqlalchemy_models import DB_URI, Base
from forestadmin.datasource_django.datasource import DjangoDatasource
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.django_agent.agent import DjangoAgent


def customize_forest(agent: DjangoAgent):
    # customize_forest_logging()

    agent.add_datasource(
        DjangoDatasource(
            support_polymorphic_relations=True, live_query_connection={"django": "default", "dj_sqlachemy": "other"}
        )
    )
    agent.add_datasource(TypicodeDatasource())
    agent.add_datasource(
        SqlAlchemyDatasource(Base, DB_URI, live_query_connection="sqlalchemy"),
    )

    agent.customize_collection("address").add_segment("France", segment_addr_fr("address"))
    agent.customize_collection("app_address").add_segment("France", segment_addr_fr("app_address"))
    agent.customize_collection("app_customer_blocked_customer").rename_field("from_customer", "from").rename_field(
        "to_customer", "to"
    )

    # # ## ADDRESS
    agent.customize_collection("app_address").add_segment(
        "highOrderDelivery", high_delivery_address_segment
    ).rename_field("country", "pays").add_field("full_address", address_full_name_computed("country")).rename_field(
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
        "number"
        # deactivate count
    ).disable_count().add_external_relation(
        "postal_code",
        {
            "schema": {
                "codePostal": "String",
                "codeCommune": "String",
                "nomCommune": "String",
                "libelleAcheminement": "String",
            },
            "list_records": get_postal_code,
            "dependencies": ["zip_code"],
        },
    )

    # cart
    agent.customize_collection("app_cart").add_field(
        "customer_id",
        {
            "column_type": "Number",
            "dependencies": ["order:customer_id"],
            "get_values": cart_get_customer_id,
        },
    ).emulate_field_operator("customer_id", "in").replace_field_writing("name", cart_update_name).add_segment(
        "No order", lambda ctx: ConditionTreeLeaf("order_id", "equal", None)
    ).emulate_field_filtering(
        "customer_id"
    )

    # # ## CUSTOMERS
    # # import field ?
    agent.customize_collection("app_customer").add_field(
        "age",
        {
            "column_type": "Number",
            "dependencies": ["birthday_date"],
            "get_values": lambda records, ctx: [
                int((datetime.date.today() - r["birthday_date"]).days / 365) for r in records
            ],
        },
    ).add_segment("with french address", french_address_segment).add_segment(
        "VIP customers",
        lambda context: ConditionTreeLeaf("is_vip", "equal", True),
        # add actions
    ).add_action(
        "Export json", export_json_action_dict
    ).add_action(
        "Age operation", age_operation_action_dict
    ).add_field(
        # # computed
        "full_name",
        customer_full_name(),
    ).replace_field_writing(
        # custom write on computed
        "full_name",
        customer_full_name_write,
    ).replace_field_operator(
        # custom operators for computed fields
        "full_name",
        "equal",
        full_name_equal,
    ).replace_field_operator(
        "full_name", "in", full_name_in
    ).replace_field_operator(
        "full_name",
        "not_in",
        full_name_not_in,
    ).replace_field_operator(
        "full_name", "like", full_name_like
    ).replace_field_operator(
        "full_name", "contains", full_name_contains
    ).replace_field_operator(
        "full_name",
        "not_contains",
        full_name_not_contains,
    ).emulate_field_filtering(
        # emulate others operators
        "full_name"
    ).add_field(
        "TotalSpending",
        customer_spending_computed(),
        # validation
        # ).add_field_validation(
        #     "age", Operator.GREATER_THAN, 0
    ).add_chart(
        # charts
        "total_orders",
        total_orders_customer_chart,
    ).add_chart(
        "orders_table", order_details
    ).add_many_to_many_relation(
        # relations
        "smart_billing_addresses",
        "app_address",
        "app_order",
        "customer_id",
        "billing_address_id",
    ).add_many_to_many_relation(
        "smart_delivering_addresses", "app_address", "app_order", "customer_id", "delivering_address_id"
    ).add_one_to_many_relation(
        "smart_carts", "app_cart", "customer_id"
    ).add_hook(
        # hooks
        "Before",
        "Create",
        hook_customer_before_create,
    ).add_hook(
        "After", "List", hook_customer_after_list
    ).add_chart(
        "nb_order_week", time_order_number_chart
    ).override_delete(
        customer_delete_override
    ).override_update(
        customer_update_override
    )

    # # ## ORDERS
    agent.customize_collection("app_order").add_segment("Pending order", pending_order_segment).add_segment(
        # segment
        "Delivered order",
        delivered_order_segment,
    ).add_segment("Rejected order", rejected_order_segment).add_segment(
        "Dispatched order", dispatched_order_segment
    ).add_segment(
        "Suspicious order", suspicious_order_segment
    ).add_segment(
        "newly_created", lambda context: ConditionTreeLeaf("ordered_at", "after", "2023-01-01")
    ).rename_field(
        # rename
        "amount",
        "cost",
    ).add_action(
        # action
        "Export json",
        export_orders_json,
    ).add_action(
        "Refund order(s)", refund_order_action
    ).add_field_validation(
        # validation
        "amount",
        "greater_than",
        0,
    ).add_field(
        # # computed
        "customer_full_name",
        get_customer_full_name_field(),
    ).import_field(
        "customer_first_name", {"path": "customer:first_name"}
    ).add_field(
        "ordered_date",
        {
            "column_type": "Date",
            "dependencies": ["ordered_at"],
            "get_values": lambda records, cts: [r["ordered_at"] for r in records],
        },
    )
    agent.customize_collection("app_tag").rename_field("tagged_item", "item")

    # general
    agent.add_chart("total_order", total_order_chart).add_chart(
        "mytablechart",
        lambda ctx, result_builder: result_builder.smart(
            [{"username": "Darth Vador", "points": 1500000}, {"username": "Luke Skywalker", "points": 2}]
        ),
    ).add_chart("total_order_week", nb_order_per_week)

    return agent
