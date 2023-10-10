import time
from ssl import Options
from threading import Thread
from typing import Dict

import urllib3
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from sseclient import SSEClient


class SSECacheInvalidation(Thread):
    _MESSAGE__CACHE_KEY: Dict[str, str] = {
        "refresh-users": ["forest.users"],
        "refresh-roles": ["forest.collections"],
        "refresh-renderings": ["forest.collections", "forest.stats", "forest.scopes"],
        # "refresh-customizations": None,  # work with nocode actions
        # TODO: add one for ip whitelist when server implement it
    }

    def __init__(self, permission_service: "PermissionService", options: Options, *args, **kwargs):  # noqa: F821
        super().__init__(name="SSECacheInvalidationThread", daemon=False, *args, **kwargs)
        self.permission_service = permission_service
        self.options: Options = options
        self.sse_client: SSEClient = None
        self._exit_thread = False

    def stop(self):
        self._exit_thread = True
        if self.sse_client:
            self.sse_client.close()

    def run(self) -> None:
        while not self._exit_thread:
            url = f"{self.options['forest_server_url']}/liana/v4/subscribe-to-events"
            headers = {"forest-secret-key": self.options["env_secret"], "Accept": "text/event-stream"}
            try:
                http = urllib3.PoolManager()
                self.sse_client = SSEClient(http.request("GET", url, preload_content=False, headers=headers))

                for msg in self.sse_client.events():
                    if msg.event == "heartbeat":
                        continue

                    if self._MESSAGE__CACHE_KEY.get(msg.event) is not None:
                        for cache_key in self._MESSAGE__CACHE_KEY[msg.event]:
                            self.permission_service.invalidate_cache(cache_key)
                        ForestLogger.log(
                            "info", f"invalidate cache {self._MESSAGE__CACHE_KEY[msg.event]} for event {msg.event}"
                        )
                    else:
                        ForestLogger.log("info", f"SSECacheInvalidationThread: unhandled message from server: {msg}")

            except Exception as exc:
                ForestLogger.log("debug", f"SSE connection to forestadmin server due to {str(exc)}")
                ForestLogger.log("warning", "SSE connection to forestadmin server closed unexpectedly, retrying.")
            time.sleep(5)
