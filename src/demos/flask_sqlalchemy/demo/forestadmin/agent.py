from demo.forestadmin.settings import SETTINGS
from demo.forestadmin.smart.address import address_full_name
from demo.forestadmin.smart.customer import (
    AgeOperation,
    ExportJson,
    customer_full_name,
    french_address_segment,
)
from demo.forestadmin.smart.order import ExportJson as ExportOrderJson
from demo.forestadmin.smart.order import (
    delivered_order_segment,
    dispatched_order_segment,
    pending_order_segment,
    rejected_order_segment,
    suspicious_order_segment,
)
from demo.models.models import Base
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.flask_agent.agent import build_agent

agent = build_agent(SETTINGS)

agent.add_datasource(SqlAlchemyDatasource(Base))

# agent.customize_collection("address").rename_field("country", "pays")  # make the register computed not work
agent.customize_collection("address").register_computed(*address_full_name())
agent.customize_collection("address").rename_field("full address", "complete_address")
# changing visibility
agent.customize_collection("address").change_field_visibility("zip_code", False)


# segment
agent.customize_collection("order").add_segment("Pending order", pending_order_segment)
agent.customize_collection("order").add_segment("Delivered order", delivered_order_segment)
agent.customize_collection("order").add_segment("Rejected order", rejected_order_segment)
agent.customize_collection("order").add_segment("Dispatched order", dispatched_order_segment)
agent.customize_collection("order").add_segment("Suspicious order", suspicious_order_segment)

# import field ?
agent.customize_collection("customer").add_segment("with french address", french_address_segment)
# action file bulk
agent.customize_collection("customer").add_action("Export json", ExportJson())
# action single with form
agent.customize_collection("customer").add_action("Age operation", AgeOperation())
agent.customize_collection("customer").register_computed(*customer_full_name())

# rename
agent.customize_collection("order").rename_field("amount", "cost")
# action file global
agent.customize_collection("order").add_action("Export json", ExportOrderJson())


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
