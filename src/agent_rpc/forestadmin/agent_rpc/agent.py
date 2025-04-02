import asyncio
import json
from uuid import UUID

from aiohttp import web
from aiohttp_sse import sse_response
from forestadmin.agent_rpc.options import RpcOptions
from forestadmin.agent_toolkit.agent import Agent
from forestadmin.agent_toolkit.options import Options
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


class RpcAgent(Agent):
    def __init__(self, options: RpcOptions):
        self.listen_addr, self.listen_port = options["listen_addr"].rsplit(":", 1)
        agent_options: Options = {**options}  # type:ignore
        agent_options["skip_schema_update"] = True
        agent_options["env_secret"] = "f" * 64
        agent_options["server_url"] = "http://fake"
        agent_options["schema_path"] = "./.forestadmin-schema.json"
        super().__init__(agent_options)

        self.app = web.Application(middlewares=[self.hmac_middleware])
        self.setup_routes()

    @web.middleware
    async def hmac_middleware(self, request: web.Request, handler):
        if request.method == "POST":
            body = await request.read()
            if not is_valid_hmac(
                self.options["auth_secret"].encode(), body, request.headers.get("X-FOREST-HMAC", "").encode("utf-8")
            ):
                return web.Response(status=401, text="Unauthorized from HMAC verification")
        return await handler(request)

    def setup_routes(self):
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
        self.app.router.add_route("GET", "/", lambda _: web.Response(text="OK"))  # type: ignore

    async def sse_handler(self, request: web.Request) -> web.StreamResponse:
        async with sse_response(request) as resp:
            while resp.is_connected():
                await resp.send("", event="heartbeat")
                await asyncio.sleep(1)
            data = json.dumps({"event": "RpcServerStop"})
            await resp.send(data, event="RpcServerStop")
        return resp

    async def schema(self, request):
        await self.customizer.get_datasource()

        return web.json_response(await SchemaSerializer(await self.customizer.get_datasource()).serialize())

    async def collection_list(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = PaginatedFilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore
        projection = ProjectionSerializer.deserialize(body_params["projection"])

        records = await collection.list(caller, filter_, projection)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    async def collection_create(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)
        ds = await self.customizer.get_datasource()

        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        data = [RecordSerializer.deserialize(r, collection) for r in body_params["data"]]  # type:ignore

        records = await collection.create(caller, data)
        records = [RecordSerializer.serialize(record) for record in records]
        return web.json_response(records)

    async def collection_update(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore
        patch = RecordSerializer.deserialize(body_params["patch"], collection)  # type:ignore

        await collection.update(caller, filter_, patch)
        return web.Response(text="OK")

    async def collection_delete(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore

        await collection.delete(caller, filter_)
        return web.Response(text="OK")

    async def collection_aggregate(self, request: web.Request):
        body_params = await request.json()
        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])
        caller = CallerSerializer.deserialize(body_params["caller"])
        filter_ = FilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore
        aggregation = AggregationSerializer.deserialize(body_params["aggregation"])

        records = await collection.aggregate(caller, filter_, aggregation)
        return web.json_response(records)

    async def collection_get_form(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])

        caller = CallerSerializer.deserialize(body_params["caller"])
        action_name = body_params["actionName"]
        if body_params["filter"]:
            filter_ = FilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore
        else:
            filter_ = None
        data = ActionFormValuesSerializer.deserialize(body_params["data"])
        meta = body_params["meta"]

        form = await collection.get_form(caller, action_name, data, filter_, meta)
        return web.json_response(ActionFormSerializer.serialize(form))

    async def collection_execute(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        collection = ds.get_collection(body_params["collectionName"])

        caller = CallerSerializer.deserialize(body_params["caller"])
        action_name = body_params["actionName"]
        if body_params["filter"]:
            filter_ = FilterSerializer.deserialize(body_params["filter"], collection)  # type:ignore
        else:
            filter_ = None
        data = ActionFormValuesSerializer.deserialize(body_params["data"])

        result = await collection.execute(caller, action_name, data, filter_)
        return web.json_response(ActionResultSerializer.serialize(result))  # type:ignore

    async def collection_render_chart(self, request: web.Request):
        body_params = await request.text()
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
        return web.json_response(result)

    async def render_chart(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()

        caller = CallerSerializer.deserialize(body_params["caller"])
        name = body_params["name"]

        result = await ds.render_chart(caller, name)
        return web.json_response(result)

    async def native_query(self, request: web.Request):
        body_params = await request.text()
        body_params = json.loads(body_params)

        ds = await self.customizer.get_datasource()
        connection_name = body_params["connectionName"]
        native_query = body_params["nativeQuery"]
        parameters = body_params["parameters"]

        result = await ds.execute_native_query(connection_name, native_query, parameters)
        return web.json_response(result)

    def start(self):
        web.run_app(self.app, host=self.listen_addr, port=int(self.listen_port))
