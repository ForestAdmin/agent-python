import asyncio
import logging

from forestadmin.agent_rpc.agent import RpcAgent
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from sqlalchemy_models import DB_URI, Base


def main() -> None:
    agent = RpcAgent({"listen_addr": "0.0.0.0:50051"})
    agent.add_datasource(
        SqlAlchemyDatasource(Base, DB_URI), {"rename": lambda collection_name: f"FROMRPCAGENT_{collection_name}"}
    )
    agent.customize_collection("FROMRPCAGENT_address").add_field(
        "new_fieeeld",
        {
            "column_type": "String",
            "dependencies": ["pk"],
            "get_values": lambda records, ctx: ["v" for r in records],
        },
    )
    agent.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # asyncio.run(main())
    main()
