import asyncio
import datetime
from typing import List

import aiohttp
from aiohttp_sse_client import client as sse_client
from forestadmin.rpc_common.hmac import generate_hmac


class RPCRequester:
    def __init__(self, connection_uri: str, secret_key: str):
        self.connection_uri = connection_uri
        self.secret_key = secret_key

    def mk_hmac_headers(self):
        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        return {
            "X_SIGNATURE": generate_hmac(self.secret_key.encode("utf-8"), timestamp.encode("utf-8")),
            "X_TIMESTAMP": timestamp,
        }

    async def sse_connect(self, callback):
        """Connect to the SSE stream."""
        await self.wait_for_connection()

        async with sse_client.EventSource(
            f"http://{self.connection_uri}/forest/rpc/sse",
        ) as event_source:
            try:
                async for event in event_source:
                    # print(event)
                    pass
            except Exception:
                pass

        await callback()

    async def wait_for_connection(self):
        """Wait for the connection to be established."""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    async with session.get(f"http://{self.connection_uri}/") as response:
                        if response.status == 200:
                            return True
                        else:
                            raise Exception(f"Failed to connect: {response.status}")
                except Exception:
                    await asyncio.sleep(1)

    # methods for datasource

    async def schema(self) -> dict:
        """Get the schema of the datasource."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://{self.connection_uri}/forest/rpc-schema",
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get schema: {response.status}")

    # TODO: speak about; it's currently not implemented in ruby
    # async def native_query(self, body):
    #     """Execute a native query."""
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(
    #             f"http://{self.connection_uri}/execute-native-query",
    #             json=body,
    #             headers=self.mk_hmac_headers(),
    #         ) as response:
    #             if response.status == 200:
    #                 return await response.json()
    #             else:
    #                 raise Exception(f"Failed to execute native query: {response.status}")

    async def datasource_render_chart(self, body):
        """Render a chart."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/datasource-chart",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to render chart: {response.status}")

    # methods for collection

    async def list(self, collection_name, body) -> list[dict]:
        """List records in a collection."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/list",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to list query: {response.status}")

    async def create(self, body) -> List[dict]:
        """Create records in a collection."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/collection/create",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to create query: {response.status}")

    async def update(self, collection_name, body):
        """Update records in a collection."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/update",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return
                else:
                    raise Exception(f"Failed to update query: {response.status}")

    async def delete(self, collection_name, body):
        """Delete records in a collection."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/delete",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return
                else:
                    raise Exception(f"Failed to delete query: {response.status}")

    async def aggregate(self, collection_name, body):
        """Aggregate records in a collection."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/aggregate",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to aggregate query: {response.status}")

    async def get_form(self, collection_name, body):
        """Get the form for an action."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/action-form",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to aggregate query: {response.status}")

    async def execute(self, collection_name, body):
        """Execute an action."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/action-execute",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to execute query: {response.status}")

    async def collection_render_chart(self, collection_name, body):
        """Render a chart."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.connection_uri}/forest/rpc/{collection_name}/chart",
                json=body,
                headers=self.mk_hmac_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to render chart: {response.status}")
