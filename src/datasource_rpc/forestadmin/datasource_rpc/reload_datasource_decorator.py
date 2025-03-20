import asyncio
import hashlib
import json

# from dictdiffer import diff as differ
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.datasource_rpc.reloadable_datasource import ReloadableDatasource
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator


class ReloadDatasourceDecorator(DatasourceDecorator):
    def __init__(self, reload_method, datasource):
        self.reload_method = reload_method
        super().__init__(datasource, CollectionDecorator)
        self.current_schema_hash = self.hash_current_schema()
        self.current_schema = {
            "charts": self.child_datasource.schema["charts"],
            "live_query_connections": self.child_datasource.get_native_query_connections(),
            "collections": [c.schema for c in sorted(self.child_datasource.collections, key=lambda c: c.name)],
        }
        self.current_schema_str = json.dumps(
            {
                "charts": self.child_datasource.schema["charts"],
                "live_query_connections": self.child_datasource.get_native_query_connections(),
                "collections": [c.schema for c in sorted(self.child_datasource.collections, key=lambda c: c.name)],
            },
            default=str,
        )
        if not isinstance(self.child_datasource, ReloadableDatasource):
            raise ValueError("The child datasource must be a ReloadableDatasource")
        self.child_datasource.trigger_reload = self.reload

    def reload(self):
        # diffs = differ(
        #     self.current_schema,
        #     {
        #         "charts": self.child_datasource.schema["charts"],
        #         "live_query_connections": self.child_datasource.get_native_query_connections(),
        #         "collections": [c.schema for c in sorted(self.child_datasource.collections, key=lambda c: c.name)],
        #     },
        # )
        if self.current_schema_hash == self.hash_current_schema():
            ForestLogger.log("info", "Schema has not changed, skipping reload")
            return

        if asyncio.iscoroutinefunction(self.reload_method):
            asyncio.run(self.reload_method())
        else:
            self.reload_method()

    def hash_current_schema(self):
        h = hashlib.shake_256(
            json.dumps(
                {
                    "charts": self.child_datasource.schema["charts"],
                    "live_query_connections": self.child_datasource.get_native_query_connections(),
                    "collections": [c.schema for c in sorted(self.child_datasource.collections, key=lambda c: c.name)],
                },
                default=str,
            ).encode("utf-8")
        )
        return h.hexdigest(20)
