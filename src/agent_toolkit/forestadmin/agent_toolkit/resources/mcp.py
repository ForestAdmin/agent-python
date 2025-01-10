from __future__ import annotations

import asyncio
import json
import logging
import os
from multiprocessing import Condition
from threading import Thread
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import (
    authenticate,
    authorize,
    check_method,
    ip_white_list,
)
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response, User
from forestadmin.agent_toolkit.utils.forest_schema.emitter import SchemaEmitter
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_composite import CompositeDatasource
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import ForbiddenError
from forestadmin.datasource_toolkit.interfaces.fields import is_column
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from mcp import types
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.server import Settings

if TYPE_CHECKING:
    from forestadmin.agent_toolkit.agent import Agent


class MCPResource(Thread):
    @staticmethod
    def create_mcp_server(agent: "Agent", datasource: Datasource) -> MCPResource:
        return MCPResource(agent, datasource)

    def __init__(self, agent: Agent, datasource: Datasource):
        self.agent = agent
        self.datasource = datasource
        self.mcp: FastMCP = FastMCP(
            "forest_agent_mcp",
            port=agent.options["mcp_server_port"],
            debug=True,
            # log_level="DEBUG",
        )

        return super().__init__(daemon=True)

    def run(self) -> None:
        if os.environ.get("RUN_MAIN") != "true":
            return
        self.setup_prompts()
        self.setup_resources()
        self.setup_tools()
        super().run()
        self.mcp.run("sse")
        ForestLogger.log("info", f'mcp server is running on port {self.agent.options["mcp_server_port"]}')
        return

    def setup_prompts(self):
        @self.mcp.prompt("prompt://ping")
        def ping():
            return [
                {
                    "role": "user",
                    "content": {
                        "type": "resource",
                        "resource": {"uri": "resource://collections", "text": "read collections"},
                    },
                }
            ]

        @self.mcp.prompt("prompt://echo")
        def echo(text: str) -> str:
            return "echo: " + text

    def setup_resources(self):
        @self.mcp.resource(
            "resource://collections",
            name="list of collections",
            description="get the list of collections known by forestadmin",
        )
        def get_collections() -> List[str]:
            ForestLogger.log("info", "-- RESOURCE get_collections")
            return [c.name for c in self.datasource.collections]

        @self.mcp.resource(
            "resource://schema",
            name="metadata of collections",
            description="get the structure of forestadmin collections, including fields, actions and segments",
        )
        def get_collection_metadata():
            ForestLogger.log("info", "-- RESOURCE get_collection_metadata")
            with open(self.agent.options["schema_path"], "r", encoding="utf-8") as schema_file:
                collection_schema = json.load(schema_file)["collections"]
            return SchemaEmitter.serialize(collection_schema, self.agent.meta)

    def setup_tools(self):
        self.setup_metadata_tools()
        self.setup_data_access_tools()
        self.setup_actions_tools()
        pass

    def setup_metadata_tools(self):
        @self.mcp.tool("list_collections")
        def get_collections(any) -> List[str]:
            """list all the collections names known by forestadmin"""
            ret = [c.name for c in self.datasource.collections]
            ForestLogger.log("info", f"-- TOOL get_collections, {ret}")
            return ret

        @self.mcp.tool("collection-fields")
        def get_fields(collection_name: str) -> List[str]:
            """list all fields and relations of collection {collection_name}"""
            ForestLogger.log("info", f"-- TOOL get_fields of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["fields"]

        @self.mcp.tool("collection-segments")
        def get_segments(collection_name: str) -> List[str]:
            """list all segments of collection {collection_name}"""
            ForestLogger.log("info", f"-- TOOL get_segments of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["segments"]

        @self.mcp.tool("collection-actions")
        def get_actions(collection_name: str) -> List[str]:
            """
            list all the actions of the collection {collection_name}.
            If there is only one field named 'Loading...' in the form, it means that the form is dynamic and you should
                use the tool load form to have it, otherwise you can trust that it is in 'form' key.
            Action are executable by using execute_action tool.
            """
            ForestLogger.log("info", f"-- TOOL get_actions of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["actions"]

    def setup_actions_tools(self):
        @self.mcp.tool("collection-load-form")
        async def load_form(collection_name: str, action_name: str) -> List[str]:
            """load form of action {action_name} of collection {collection_name}."""
            ForestLogger.log("info", f"-- TOOL load form of action {action_name} of collection {collection_name}")
            try:
                form = await cast(Collection, self.datasource.get_collection(collection_name)).get_form(
                    None, action_name, {}, None, None
                )
                ForestLogger.log("info", f"-- TOOL load form of action of {collection_name}: {form} ")
                return form
            except Exception as exc:
                ForestLogger.log("exception", f"mcp execute error {exc}")
                return str(exc)

        @self.mcp.tool("collection-execute-action")
        async def execute_action(
            collection_name: str,
            action_name: str,
            record_id: Optional[Union[Any, List[Any]]] = None,
            form: Optional[Any] = None,
        ) -> List[str]:
            """execute action {action_name} of collection {collection_name}, with form {form}.
            Actions can be found using collection-actions tool.
            If there is a form, it must be filled, and given in {form}, and {form} must be formatted as: '{"label": "value"}'.
            Be sure the user verified the form before calling this tool.
            """
            ForestLogger.log(
                "info",
                f"-- TOOL execute of action {action_name} of collection {collection_name}. form is {form}. record id is {record_id}",
            )
            if action_name not in self.datasource.get_collection(collection_name).schema["actions"]:
                raise Exception(
                    f"Action {action_name} not found in collection {collection_name}, "
                    f"actions are {', '.join(self.datasource.get_collection(collection_name).schema['actions'].keys())}"
                )
            form = form or {}
            filter_ = Filter({})
            if record_id:
                filter_ = filter_.override(
                    {
                        "condition_tree": ConditionTreeLeaf(
                            SchemaUtils.get_primary_keys(self.datasource.get_collection(collection_name).schema)[0],
                            "in",
                            record_id if isinstance(record_id, list) else [record_id],
                        )
                    }
                )
            try:
                ret = await cast(Collection, self.datasource.get_collection(collection_name)).execute(
                    None, action_name, form, filter_
                )
                ForestLogger.log("info", f"-- TOOL execute of action of {collection_name}: {str(ret)} ")
                return ret
            except Exception as exc:
                ForestLogger.log("exception", f"mcp execute error {exc}")
                return str(exc)

    def setup_data_access_tools(self):
        @self.mcp.tool("list-collection-records")
        async def list(collection_name: str) -> List[Dict[str, Any]]:
            """list records of {collection_name}. collection_name can be found using get_collections tool"""
            ForestLogger.log("info", f"-- TOOL get_list of {collection_name}")
            ret = await self.datasource.get_collection(collection_name).list(
                None,
                PaginatedFilter({}),
                ProjectionFactory.all(self.datasource.get_collection(collection_name)),
            )
            ForestLogger.log("info", f"-- TOOL get_list of {collection_name} ; {len(ret)} records")
            # await ctx.report_progress(100, 100)
            return ret

        @self.mcp.tool("search-in-collection")
        async def search(collection_name: str, search: Union[int, float, str, Dict[str, Any]]) -> List[Dict[str, Any]]:
            """
            search in collection {collection_name} for entry matching {search}.
            collection_name can be found using get_collections tool
            """
            ForestLogger.log("info", f"-- TOOL search({search}) of {collection_name}")
            filter_ = PaginatedFilter({})
            schema = self.datasource.get_collection(collection_name).schema
            if isinstance(search, dict):
                available_fields = [field for field in schema["fields"].keys() if is_column(schema["fields"][field])]
                for key, value in search.items():
                    if key not in schema["fields"]:
                        raise Exception(
                            f"Field {key} not found in collection {collection_name}, fields are {', '.join(available_fields)}"
                        )
                    if not is_column(schema["fields"][key]):
                        raise Exception(
                            f"Field {key} is a relation in collection {collection_name}, you must search over columns: "
                            f"{', '.join(available_fields)}"
                        )

                filter_ = filter_.override(
                    {
                        "condition_tree": ConditionTreeFactory.intersect(
                            [ConditionTreeLeaf(key, "equal", value) for key, value in search.items()]
                        )
                    }
                )
            else:
                filter_ = filter_.override({"search": str(search)})

            try:
                ret = await self.datasource.get_collection(collection_name).list(
                    None,
                    filter_,
                    ProjectionFactory.all(self.datasource.get_collection(collection_name)),
                )
                ForestLogger.log("info", f"-- TOOL search({search}) of {collection_name} ; {len(ret)} records")
                return ret
            except Exception as exc:
                ForestLogger.log("exception", f"mcp execute error {exc}")
