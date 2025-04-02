import asyncio
import hashlib
import json
from threading import Thread
from typing import Any, Dict

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_rpc.collection import RPCCollection
from forestadmin.datasource_rpc.requester import RPCRequester
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function
from forestadmin.rpc_common.serializers.schema.schema import SchemaDeserializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer


def _hash_schema(schema) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()


async def create_rpc_datasource(connection_uri: str, secret_key: str, reload_method=None) -> "RPCDatasource":
    """Create a new RPC datasource and wait for the connection to be established."""
    datasource = RPCDatasource(connection_uri, secret_key, reload_method)
    await datasource.wait_for_connection()
    await datasource.introspect()
    return datasource


class RPCDatasource(Datasource):
    def __init__(self, connection_uri: str, secret_key: str, reload_method=None):
        super().__init__([])
        self.connection_uri = connection_uri
        self.reload_method = reload_method
        self.secret_key = secret_key
        self.last_schema_hash = ""

        self.requester = RPCRequester(connection_uri, secret_key)

        # self.thread = Thread(target=asyncio.run, args=(self.run(),), name="RPCDatasourceSSEThread", daemon=True)
        self.thread = Thread(
            target=asyncio.run,
            args=(self.requester.sse_connect(self.sse_callback),),
            name="RPCDatasourceSSEThread",
            daemon=True,
        )
        self.thread.start()

    async def introspect(self) -> bool:
        """return true if schema has changed"""
        schema_data = await self.requester.schema()
        if self.last_schema_hash == _hash_schema(schema_data):
            ForestLogger.log("debug", "[RPCDatasource] Schema has not changed")
            return False
        self.last_schema_hash = _hash_schema(schema_data)

        self._collections = {}
        self._schema = {"charts": {}}
        schema_data = SchemaDeserializer().deserialize(schema_data)
        for collection_name, collection in schema_data["collections"].items():
            self.create_collection(collection_name, collection)

        self._schema["charts"] = {name: None for name in schema_data["charts"]}  # type: ignore
        self._live_query_connections = schema_data["live_query_connections"]
        return True

    def create_collection(self, collection_name, collection_schema):
        collection = RPCCollection(collection_name, self)
        for name, field in collection_schema["fields"].items():
            collection.add_field(name, field)

        if len(collection_schema["actions"]) > 0:
            for action_name, action_schema in collection_schema["actions"].items():
                collection.add_rpc_action(action_name, action_schema)

        collection._schema["charts"] = {name: None for name in collection_schema["charts"]}  # type: ignore
        collection.add_segments(collection_schema["segments"])

        if collection_schema["countable"]:
            collection.enable_count()
        collection.enable_search()

        self.add_collection(collection)

    async def wait_for_connection(self):
        """Wait for the connection to be established."""
        await self.requester.wait_for_connection()
        ForestLogger.log("debug", "Connection to RPC datasource established")

    async def internal_reload(self):
        has_changed = await self.introspect()
        if has_changed and self.reload_method is not None:
            await call_user_function(self.reload_method)

    async def sse_callback(self):
        await self.wait_for_connection()
        await self.internal_reload()

        self.thread = Thread(
            target=asyncio.run,
            args=(self.requester.sse_connect(self.sse_callback),),
            name="RPCDatasourceSSEThread",
            daemon=True,
        )
        self.thread.start()

    # TODO: speak about; it's currently not implemented in ruby
    # async def execute_native_query(self, connection_name: str, native_query: str, parameters: Dict[str, str]) -> Any:
    #     return await self.requester.native_query(
    #         {
    #             "connectionName": connection_name,
    #             "nativeQuery": native_query,
    #             "parameters": parameters,
    #         }
    #     )
    async def execute_native_query(self, connection_name: str, native_query: str, parameters: Dict[str, str]) -> Any:
        raise NotImplementedError

    async def render_chart(self, caller: User, name: str) -> Chart:
        if name not in self._schema["charts"].keys():
            raise ValueError(f"Chart {name} does not exist in this datasource")

        body = {
            "caller": CallerSerializer.serialize(caller) if caller is not None else None,
            "name": name,
        }

        response = self.requester.collection_render_chart(body)
        return response
