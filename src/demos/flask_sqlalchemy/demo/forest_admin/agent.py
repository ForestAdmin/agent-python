from demo.forest_admin.settings import SETTINGS
from demo.forest_admin.smart.address import address_full_name_computed, high_delivery_address_segment
from demo.forest_admin.smart.customer import (  # computed_full_address_caps,
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
from forestadmin.flask_agent.agent import build_agent

agent = build_agent(SETTINGS)
agent.add_datasource(SqlAlchemyDatasource(Base))


# ## ADDRESS
agent.customize_collection("address").add_segment("highOrderDelivery", high_delivery_address_segment)

# agent.customize_collection("address").rename_field("country", "pays")  # make the register computed not work
agent.customize_collection("address").register_computed("full address", address_full_name_computed("country"))
# agent.customize_collection("address").register_computed("full address", address_full_name_computed("pays"))

agent.customize_collection("address").rename_field("full address", "complete_address")
# changing visibility
agent.customize_collection("address").change_field_visibility("zip_code", False)

# ## CUSTOMERS
# import field ?
agent.customize_collection("customer").add_segment("with french address", french_address_segment)
# action file bulk
agent.customize_collection("customer").add_action("Export json", ExportJson())
# action single with form
agent.customize_collection("customer").add_action("Age operation", AgeOperation())

agent.customize_collection("customer").register_computed("full_name", customer_full_name())
# agent.customize_collection("customer").register_computed("TotalSpending", customer_spending_computed())


# ## ORDERS
# segment
# agent.customize_collection("order").rename_field("amount", "cost")
# agent.customize_collection("order").add_segment("Pending order", pending_order_segment)
# agent.customize_collection("order").add_segment("Delivered order", delivered_order_segment)
# agent.customize_collection("order").add_segment("Rejected order", rejected_order_segment)
# agent.customize_collection("order").add_segment("Dispatched order", dispatched_order_segment)
# agent.customize_collection("order").add_segment("Suspicious order", suspicious_order_segment)

# rename
# agent.customize_collection("order").register_computed("customer\\ full_name", get_customer_full_name_field())
# action file global
# agent.customize_collection("order").add_action("Export json", ExportOrderJson())

# deactivate count

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
