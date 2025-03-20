import asyncio
import logging

import grpc
from forestadmin.rpc_common.proto import datasource_pb2, datasource_pb2_grpc
from google.protobuf import empty_pb2


async def run() -> None:
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = datasource_pb2_grpc.DataSourceStub(channel)
        response = await stub.Schema(empty_pb2.Empty())
    print(response)
    print("datasource client received: " + str(response.Collections[0].searchable))


if __name__ == "__main__":
    logging.basicConfig()
    asyncio.run(run())
