from app.forest.customer import get_customer_spent_values
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.django_agent.agent import DjangoAgent


def customize_forest(agent: DjangoAgent):
    agent.customize_collection("Cart").add_field(
        "customer_id",
        {
            "dependencies": ["order:customer_id"],
            "column_type": PrimitiveType.NUMBER,
            "get_values": lambda records, context: [rec["order"]["customer_id"] for rec in records],
        },
    ).emulate_field_filtering("customer_id")
    agent.customize_collection("Customer").add_field(
        "total_spending",
        {"column_type": PrimitiveType.NUMBER, "dependencies": ["id"], "get_values": get_customer_spent_values},
    ).add_one_to_many_relation("smart_carts", "Cart", "customer_id").add_many_to_many_relation(
        # relations
        "smart_billing_addresses",
        "Address",
        "Order",
        "customer_id",
        "billing_address_id",
    )
