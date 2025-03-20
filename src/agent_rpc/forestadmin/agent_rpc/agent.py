import asyncio
import json
import os
import pprint
import signal
import sys
import threading
import time
from enum import Enum

from aiohttp import web
from aiohttp_sse import sse_response

# import grpc
from forestadmin.agent_rpc.options import RpcOptions

# from forestadmin.agent_rpc.services.datasource import DatasourceService
from forestadmin.agent_toolkit.agent import Agent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_toolkit.interfaces.fields import is_column
from forestadmin.rpc_common.serializers.collection.aggregation import AggregationSerializer
from forestadmin.rpc_common.serializers.collection.filter import (
    FilterSerializer,
    PaginatedFilterSerializer,
    ProjectionSerializer,
)
from forestadmin.rpc_common.serializers.collection.record import RecordSerializer
from forestadmin.rpc_common.serializers.schema.schema import SchemaSerializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer

# from concurrent import futures


# from forestadmin.rpc_common.proto import datasource_pb2_grpc


class RcpJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, set):
            return list(sorted(o, key=lambda x: x.value if isinstance(x, Enum) else str(x)))
        if isinstance(o, set):
            return list(sorted(o, key=lambda x: x.value if isinstance(x, Enum) else str(x)))

        try:
            return super().default(o)
        except Exception as exc:
            print(f"error on seriliaze {o}, {type(o)}: {exc}")


class RpcAgent(Agent):
    # TODO: options to add:
    # * listen addr
    def __init__(self, options: RpcOptions):
        # self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        # self.server = grpc.aio.server()
        self.listen_addr, self.listen_port = options["listen_addr"].rsplit(":", 1)
        self.app = web.Application()
        # self.server.add_insecure_port(options["listen_addr"])
        options["skip_schema_update"] = True
        options["env_secret"] = "f" * 64
        options["server_url"] = "http://fake"
        options["auth_secret"] = "fake"
        options["schema_path"] = "./.forestadmin-schema.json"

        super().__init__(options)
        self._server_stop = False
        self.setup_routes()
        # signal.signal(signal.SIGUSR1, self.stop_handler)

    def setup_routes(self):
        self.app.router.add_route("GET", "/sse", self.sse_handler)
        self.app.router.add_route("GET", "/schema", self.schema)
        self.app.router.add_route("POST", "/collection/list", self.collection_list)
        self.app.router.add_route("POST", "/collection/create", self.collection_create)
        self.app.router.add_route("POST", "/collection/update", self.collection_update)
        self.app.router.add_route("POST", "/collection/delete", self.collection_delete)
        self.app.router.add_route("POST", "/collection/aggregate", self.collection_aggregate)
        self.app.router.add_route("GET", "/", lambda _: web.Response(text="OK"))

    async def sse_handler(self, request: web.Request) -> web.StreamResponse:
        async with sse_response(request) as resp:
            while resp.is_connected() and not self._server_stop:
                await resp.send("", event="heartbeat")
                await asyncio.sleep(1)
            data = json.dumps({"event": "RpcServerStop"})
            await resp.send(data, event="RpcServerStop")
        return resp

    async def schema(self, request):
        await self.customizer.get_datasource()

        return web.Response(text=await SchemaSerializer(await self.customizer.get_datasource()).serialize())

    async def collection_list(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = PaginatedFilterSerializer.deserialize(body_params["filter"], collection)
        projection = ProjectionSerializer.deserialize(body_params["projection"])

        records = await collection.list(caller, filter_, projection)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    async def collection_create(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        data = [RecordSerializer.deserialize(r, collection) for r in body_params["data"]]

        records = await collection.create(caller, data)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    async def collection_update(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)
        patch = RecordSerializer.deserialize(body_params["patch"], collection)

        await collection.update(caller, filter_, patch)
        return web.Response(text="OK")

    async def collection_delete(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)

        await collection.delete(caller, filter_)
        return web.Response(text="OK")

    async def collection_aggregate(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)
        aggregation = AggregationSerializer.deserialize(body_params["aggregation"])

        records = await collection.aggregate(caller, filter_, aggregation)
        # records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    def start(self):
        web.run_app(self.app, host=self.listen_addr, port=int(self.listen_port))
