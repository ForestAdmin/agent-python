import asyncio
import json
from enum import Enum
from uuid import UUID

from aiohttp import web
from aiohttp_sse import sse_response

# import grpc
from forestadmin.agent_rpc.options import RpcOptions

# from forestadmin.agent_rpc.services.datasource import DatasourceService
from forestadmin.agent_toolkit.agent import Agent
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.rpc_common.hmac import is_valid_hmac
from forestadmin.rpc_common.serializers.actions import (
    ActionFormSerializer,
    ActionFormValuesSerializer,
    ActionResultSerializer,
)
from forestadmin.rpc_common.serializers.aes import aes_decrypt, aes_encrypt
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
        self.app = web.Application(middlewares=[self.hmac_middleware])
        # self.server.add_insecure_port(options["listen_addr"])
        options["skip_schema_update"] = True
        options["env_secret"] = "f" * 64
        options["server_url"] = "http://fake"
        # options["auth_secret"] = "f48186505a3c5d62c27743126d6a76c1dd8b3e2d8897de19"
        options["schema_path"] = "./.forestadmin-schema.json"
        super().__init__(options)

        self.aes_key = self.options["auth_secret"][:16].encode()
        self.aes_iv = self.options["auth_secret"][-16:].encode()
        self._server_stop = False
        self.setup_routes()
        # signal.signal(signal.SIGUSR1, self.stop_handler)

    @web.middleware
    async def hmac_middleware(self, request: web.Request, handler):
        if request.method == "POST":
            body = await request.read()
            if not is_valid_hmac(
                self.options["auth_secret"].encode(), body, request.headers.get("X-FOREST-HMAC", "").encode("utf-8")
            ):
                return web.Response(status=401)
        return await handler(request)

    def setup_routes(self):
        # self.app.middlewares.append(self.hmac_middleware)
        self.app.router.add_route("GET", "/sse", self.sse_handler)
        self.app.router.add_route("GET", "/schema", self.schema)
        self.app.router.add_route("POST", "/collection/list", self.collection_list)
        self.app.router.add_route("POST", "/collection/create", self.collection_create)
        self.app.router.add_route("POST", "/collection/update", self.collection_update)
        self.app.router.add_route("POST", "/collection/delete", self.collection_delete)
        self.app.router.add_route("POST", "/collection/aggregate", self.collection_aggregate)
        self.app.router.add_route("POST", "/collection/get-form", self.collection_get_form)
        self.app.router.add_route("POST", "/collection/execute", self.collection_execute)
        self.app.router.add_route("POST", "/collection/render-chart", self.collection_render_chart)

        self.app.router.add_route("POST", "/execute-native-query", self.native_query)
        self.app.router.add_route("POST", "/render-chart", self.render_chart)
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

        return web.Response(text=json.dumps(await SchemaSerializer(await self.customizer.get_datasource()).serialize()))

    async def collection_list(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = PaginatedFilterSerializer.deserialize(body_params["filter"], collection)
        projection = ProjectionSerializer.deserialize(body_params["projection"])

        records = await collection.list(caller, filter_, projection)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.Response(text=aes_encrypt(json.dumps(records), self.aes_key, self.aes_iv))

    async def collection_create(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)
        ds = await self.customizer.get_datasource()

        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        data = [RecordSerializer.deserialize(r, collection) for r in body_params["data"]]

        records = await collection.create(caller, data)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    async def collection_update(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

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
        return web.Response(text=aes_encrypt(json.dumps(records), self.aes_key, self.aes_iv))

    async def collection_get_form(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])

        caller = CallerSerializer.deserialize(body_params["caller"]) if body_params["caller"] else None
        action_name = body_params["actionName"]
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection) if body_params["filter"] else None
        data = ActionFormValuesSerializer.deserialize(body_params["data"])
        meta = body_params["meta"]

        form = await collection.get_form(caller, action_name, data, filter_, meta)
        return web.Response(
            text=aes_encrypt(json.dumps(ActionFormSerializer.serialize(form)), self.aes_key, self.aes_iv)
        )

    async def collection_execute(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])

        caller = CallerSerializer.deserialize(body_params["caller"]) if body_params["caller"] else None
        action_name = body_params["actionName"]
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection) if body_params["filter"] else None
        data = ActionFormValuesSerializer.deserialize(body_params["data"])

        result = await collection.execute(caller, action_name, data, filter_)
        return web.Response(
            text=aes_encrypt(json.dumps(ActionResultSerializer.serialize(result)), self.aes_key, self.aes_iv)
        )

    async def collection_render_chart(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])

        caller = CallerSerializer.deserialize(body_params["caller"])
        name = body_params["name"]
        record_id = body_params["recordId"]
        ret = []
        for i, value in enumerate(record_id):
            type_record_id = collection.schema["fields"][SchemaUtils.get_primary_keys(collection.schema)[i]][
                "column_type"
            ]

            if type_record_id == PrimitiveType.DATE:
                ret.append(value.fromisoformat())
            elif type_record_id == PrimitiveType.DATE_ONLY:
                ret.append(value.fromisoformat())
            elif type_record_id == PrimitiveType.DATE:
                ret.append(value.fromisoformat())
            elif type_record_id == PrimitiveType.POINT:
                ret.append((value[0], value[1]))
            elif type_record_id == PrimitiveType.UUID:
                ret.append(UUID(value))
            else:
                ret.append(value)

        result = await collection.render_chart(caller, name, record_id)
        return web.Response(text=aes_encrypt(json.dumps(result), self.aes_key, self.aes_iv))

    async def render_chart(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()

        caller = CallerSerializer.deserialize(body_params["caller"])
        name = body_params["name"]

        result = await ds.render_chart(caller, name)
        return web.Response(text=aes_encrypt(json.dumps(result), self.aes_key, self.aes_iv))

    async def native_query(self, request: web.Request):
        body_params = await request.text()
        body_params = aes_decrypt(body_params, self.aes_key, self.aes_iv)
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        connection_name = body_params["connectionName"]
        native_query = body_params["nativeQuery"]
        parameters = body_params["parameters"]

        result = await ds.execute_native_query(connection_name, native_query, parameters)
        return web.Response(text=aes_encrypt(json.dumps(result), self.aes_key, self.aes_iv))

    def start(self):
        web.run_app(self.app, host=self.listen_addr, port=int(self.listen_port))
