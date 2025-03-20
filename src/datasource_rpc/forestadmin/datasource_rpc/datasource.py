import asyncio
import json
import os
import signal
import time
from threading import Thread, Timer

import grpc
import urllib3
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_rpc.collection import RPCCollection
from forestadmin.datasource_rpc.reloadable_datasource import ReloadableDatasource
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.rpc_common.serializers.schema.schema import SchemaDeserializer
from sseclient import SSEClient

# from forestadmin.rpc_common.proto import datasource_pb2_grpc
# from google.protobuf import empty_pb2


class RPCDatasource(Datasource, ReloadableDatasource):
    def __init__(self, connection_uri: str):
        super().__init__([])
        self.connection_uri = connection_uri
        # res = asyncio.run(self.connect_sse())
        # Timer(5, self.internal_reload).start()
        # self.trigger_reload()
        self.http = urllib3.PoolManager()
        self.wait_for_reconnect()
        self.introspect()
        self.thread = Thread(target=self.run, name="RPCDatasourceSSEThread", daemon=True)
        self.thread.start()

    def introspect(self):
        self._collections = {}
        self._schema = {"charts": {}}
        response = self.http.request("GET", f"http://{self.connection_uri}/schema")
        # schema_data = json.loads(response.data.decode("utf-8"))
        schema_data = SchemaDeserializer().deserialize(response.data.decode("utf-8"))
        for collection_name, collection in schema_data["collections"].items():
            self.create_collection(collection_name, collection)

        self._schema["charts"] = {name: None for name in schema_data["charts"]}
        self._live_query_connections = schema_data["live_query_connections"]

    def create_collection(self, collection_name, collection_schema):
        collection = RPCCollection(collection_name, self, self.connection_uri)
        for name, field in collection_schema["fields"].items():
            collection.add_field(name, field)
        self.add_collection(collection)

    def run(self):
        self.wait_for_reconnect()
        self.sse_client = SSEClient(
            self.http.request("GET", f"http://{self.connection_uri}/sse", preload_content=False)
        )
        try:
            for msg in self.sse_client.events():
                if msg.event == "heartbeat":
                    continue

                if msg.event == "RpcServerStop":
                    print("RpcServerStop")
                    break
        except:
            pass
        print("rpc connection to server closed")
        self.wait_for_reconnect()
        self.internal_reload()

        self.thread = Thread(target=self.run, name="RPCDatasourceSSEThread", daemon=True)
        self.thread.start()

        # self.channel = grpc.aio.insecure_channel(self.connection_uri)
        # async with grpc.aio.insecure_channel(self.connection_uri) as channel:
        # stub = datasource_pb2_grpc.DataSourceStub(self.channel)
        # response = await stub.Schema(empty_pb2.Empty())
        # self.channel

        return

    def wait_for_reconnect(self):
        while True:
            try:
                self.ping_connect()
                break
            except:
                time.sleep(1)
        print("reconntected")

    def connect(self):
        self.ping_connect()

    def ping_connect(self):
        self.http.request("GET", f"http://{self.connection_uri}/")

    def internal_reload(self):
        # Timer(5, self.internal_reload).start()
        print("trigger reload")
        self.introspect()
        self.trigger_reload()

    # def reload_agent(self):
    #     os.kill(os.getpid(), signal.SIGUSR1)
    async def render_chart(self, caller: User, name: str) -> Chart:
        raise Exception("Not implemented")
