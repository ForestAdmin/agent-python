from demo.forest_admin.settings import SETTINGS
from demo.forest_admin.smart.address import address_full_name_computed, high_delivery_address_segment
from demo.forest_admin.smart.customer import (
    AgeOperation,
    ExportJson,
    customer_full_name,
    customer_spending_computed,
    french_address_segment,
)
from demo.forest_admin.smart.order import ExportJson as ExportOrderJson
from demo.forest_admin.smart.order import (
    delivered_order_segment,
    dispatched_order_segment,
    get_customer_full_name_field,
    pending_order_segment,
    rejected_order_segment,
    suspicious_order_segment,
)
from demo.models.models import Base
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.flask_agent.agent import build_agent

agent = build_agent(SETTINGS)
agent.add_datasource(SqlAlchemyDatasource(Base))


# # ## ADDRESS
agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment)

# agent.customize_collection("address").rename_field("country", "pays")
agent.customize_collection("address").register_computed("full_address", address_full_name_computed("country"))
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
agent.customize_collection("customer").register_computed("full_name", customer_full_name())
agent.customize_collection("customer").register_computed("TotalSpending", customer_spending_computed())
# # validation
agent.customize_collection("customer").add_validation("age", {"operator": Operator.GREATER_THAN, "value": 0})


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
agent.customize_collection("order").register_computed("customer_full_name", get_customer_full_name_field())


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
