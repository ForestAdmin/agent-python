import asyncio
import hashlib
import json
import time
from threading import Thread
from typing import Any, Dict

import urllib3
from forestadmin.agent_toolkit.agent import Agent
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_rpc.collection import RPCCollection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function
from forestadmin.rpc_common.hmac import generate_hmac
from forestadmin.rpc_common.serializers.aes import aes_decrypt, aes_encrypt
from forestadmin.rpc_common.serializers.schema.schema import SchemaDeserializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer
from sseclient import SSEClient


def hash_schema(schema) -> str:
    return hashlib.sha256(json.dumps(schema, sort_keys=True).encode()).hexdigest()


class RPCDatasource(Datasource):
    def __init__(self, connection_uri: str, secret_key: str, reload_method=None):
        super().__init__([])
        self.connection_uri = connection_uri
        self.reload_method = reload_method
        self.secret_key = secret_key
        self.aes_key = secret_key[:16].encode()
        self.aes_iv = secret_key[-16:].encode()
        self.last_schema_hash = ""

        self.http = urllib3.PoolManager()
        self.wait_for_connection()
        self.introspect()

        self.thread = Thread(target=asyncio.run, args=(self.run(),), name="RPCDatasourceSSEThread", daemon=True)
        self.thread.start()

    def introspect(self) -> bool:
        """return true if schema has changed"""
        response = self.http.request("GET", f"http://{self.connection_uri}/schema")
        schema_data = json.loads(response.data.decode("utf-8"))
        if self.last_schema_hash == hash_schema(schema_data):
            ForestLogger.log("debug", "[RPCDatasource] Schema has not changed")
            return False
        self.last_schema_hash = hash_schema(schema_data)

        self._collections = {}
        self._schema = {"charts": {}}
        schema_data = SchemaDeserializer().deserialize(schema_data)
        for collection_name, collection in schema_data["collections"].items():
            self.create_collection(collection_name, collection)

        self._schema["charts"] = {name: None for name in schema_data["charts"]}
        self._live_query_connections = schema_data["live_query_connections"]
        return True

    def create_collection(self, collection_name, collection_schema):
        collection = RPCCollection(collection_name, self, self.connection_uri, self.secret_key)
        for name, field in collection_schema["fields"].items():
            collection.add_field(name, field)

        if len(collection_schema["actions"]) > 0:
            for action_name, action_schema in collection_schema["actions"].items():
                collection.add_rpc_action(action_name, action_schema)

        collection._schema["charts"] = {name: None for name in collection_schema["charts"]}

        self.add_collection(collection)

    def wait_for_connection(self):
        while True:
            try:
                self.http.request("GET", f"http://{self.connection_uri}/")
                break
            except Exception:
                time.sleep(1)
        ForestLogger.log("debug", "Connection to RPC datasource established")

    async def internal_reload(self):
        has_changed = self.introspect()
        if has_changed and self.reload_method is not None:
            await call_user_function(self.reload_method)

    async def run(self):
        self.wait_for_connection()
        self.sse_client = SSEClient(
            self.http.request("GET", f"http://{self.connection_uri}/sse", preload_content=False)
        )
        try:
            for msg in self.sse_client.events():
                pass
        except Exception:
            pass
        ForestLogger.log("info", "rpc connection to server closed")
        self.wait_for_connection()
        await self.internal_reload()

        self.thread = Thread(target=asyncio.run, args=(self.run(),), name="RPCDatasourceSSEThread", daemon=True)
        self.thread.start()

    async def execute_native_query(self, connection_name: str, native_query: str, parameters: Dict[str, str]) -> Any:
        body = aes_encrypt(
            json.dumps(
                {
                    "connectionName": connection_name,
                    "nativeQuery": native_query,
                    "parameters": parameters,
                }
            ),
            self.aes_key,
            self.aes_iv,
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/execute-native-query",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        ret = json.loads(ret)
        return ret

    async def render_chart(self, caller: User, name: str) -> Chart:
        if name not in self._schema["charts"].keys():
            raise ValueError(f"Chart {name} does not exist in this datasource")

        body = aes_encrypt(
            json.dumps(
                {
                    "caller": CallerSerializer.serialize(caller) if caller is not None else None,
                    "name": name,
                }
            ),
            self.aes_key,
            self.aes_iv,
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/render-chart",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        ret = json.loads(ret)
        return ret
