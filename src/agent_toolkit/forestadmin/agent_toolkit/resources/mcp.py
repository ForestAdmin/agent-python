from __future__ import annotations

import json
import os
from threading import Thread
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional, Union, cast

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
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import BranchComponents
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf, LeafComponents
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.page import PlainPage
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.projection import ProjectionValidator
from mcp import types
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.server import Settings
from pydantic import Field

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
        # self.setup_prompts()
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

        # @self.mcp._mcp_server.list_tools()
        # async def list_tools() -> List[types.Tool]:
        #     # help debug schema
        #     tools = await self.mcp.list_tools()
        #     # list_record_tool = [t for t in tools if t.name == "list-collection-records"][0]
        #     try:
        #         with open(
        #             os.path.abspath(os.path.join(self.agent.options["schema_path"], "..", "mcp_tools.json")), "w"
        #         ) as fout:
        #             json.dump([t.model_dump() for t in tools], fout, indent=4)
        #     except Exception as exc:
        #         print(exc)
        #     return tools

    def setup_metadata_tools(self):
        @self.mcp.tool("list_collections")
        async def get_collections() -> List[str]:
            """
            List all the collections names known by forestadmin.
            For each collection, check for:
                'Fields' using 'collection-field' tools.
                'Segments' using 'collection-segments' tool.
                'Actions' using 'collection-actions' tool.
            """
            ret = [c.name for c in self.datasource.collections]
            ForestLogger.log("info", f"-- TOOL get_collections, {ret}")
            return ret

        @self.mcp.tool("collection-fields")
        def get_fields(
            collection_name: Annotated[str, Field(description="the name of the collection you want the fields")]
        ) -> List[str]:
            """list all fields and relations of collection {collection_name}, and their definitions"""
            ForestLogger.log("info", f"-- TOOL get_fields of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["fields"]

        @self.mcp.tool("collection-segments")
        def get_segments(
            collection_name: Annotated[str, Field(description="the name of the collection you want the segments")]
        ) -> List[str]:
            """
            List all segments of collection {collection_name}.
            """
            # A Segment is a subset of a Collection: it's a saved filter of your Collection.
            ForestLogger.log("info", f"-- TOOL get_segments of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["segments"]

        @self.mcp.tool("collection-actions")
        def get_actions(
            collection_name: Annotated[str, Field(description="the name of the collection you want the actions")]
        ) -> List[str]:
            """
            list all the actions of the collection {collection_name}.
            If there is only one field named 'Loading...' in the form, it means that the form is dynamic and you should
                use the tool load form to have it, otherwise you can trust that it is in 'form' key.
            Action are executable by using execute_action tool.
            LLM should read this documentation https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/actions.
            """
            ForestLogger.log("info", f"-- TOOL get_actions of {collection_name}")
            return self.datasource.get_collection(collection_name).schema["actions"]

    def setup_actions_tools(self):
        @self.mcp.tool("collection-load-form")
        async def load_form(
            collection_name: Annotated[
                str, Field(description="the name of the collection you want the the form for action {action_name}")
            ],
            action_name: Annotated[
                str, Field(description="the name of the action in collection {collection_name} you want the form")
            ],
        ) -> List[str]:
            """
            load form of action {action_name} of collection {collection_name}.
            If there is a form associated to this action, LLM must prompt the user to fill the form.
            """
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
            collection_name: Annotated[
                str, Field(description="the name of the collection you want execute {action_name} action")
            ],
            action_name: Annotated[
                str, Field(description="the name of the action you want to execute on collection {collection_name}")
            ],
            record_id: Annotated[
                Optional[Union[Any, List[Any]]],
                Field(
                    description="the record id to execute the action if action scope is 'Single', "
                    "when action scope is 'bulk', this parameter should be a list of record ids, "
                    "and when action scope is global, this parameter should be None",
                    default=None,
                ),
            ],
            form: Annotated[
                Optional[Dict[str, Any]],
                Field(
                    description="when the action provides a form, the form to fill for the action. "
                    "All fields with 'is_required=true must be filled by the end user."
                    "LLM should prompt the user to fill the form.",
                    examples=[{"label": "value"}],
                    default=None,
                ),
            ],
        ) -> List[str]:
            """execute action {action_name} of collection {collection_name}, with form {form}.
            Actions can be found using collection-actions tool.
            If there is a form, it must be filled, and given in {form}, and {form} must be
            formatted as:'{"label": "value"}'.
            Be sure the user verified the form before calling this tool.
            """
            ForestLogger.log(
                "info",
                f"-- TOOL execute of action {action_name} of collection {collection_name}. form is {form}. record id is {record_id}",
            )
            collection = self.datasource.get_collection(collection_name)
            if action_name not in collection.schema["actions"]:
                raise Exception(
                    f"Action {action_name} not found in collection {collection_name}, "
                    f"actions are {', '.join(collection.schema['actions'].keys())}"
                )
            action = collection.schema["actions"][action_name]
            if action.scope.value == "Single" and (not record_id or isinstance(record_id, list)):
                raise Exception("record id must be an unique id")
            if action.scope.value == "Bulk" and (not record_id or not isinstance(record_id, list)):
                raise Exception("record id must be a list of ids")
            form = form or {}
            filter_ = Filter({})
            if record_id:
                filter_ = filter_.override(
                    {
                        "condition_tree": ConditionTreeLeaf(
                            SchemaUtils.get_primary_keys(collection.schema)[0],
                            "in",
                            record_id if isinstance(record_id, list) else [record_id],
                        )
                    }
                )
            try:
                ret = await cast(Collection, collection).execute(None, action_name, form, filter_)
                ForestLogger.log("info", f"-- TOOL execute of action of {collection_name}: {str(ret)} ")
                return ret
            except Exception as exc:
                ForestLogger.log("exception", f"mcp execute error {exc}")
                return str(exc)

    def setup_data_access_tools(self):
        @self.mcp.tool("list-collection-records")
        async def list(
            collection_name: Annotated[
                str,
                Field(
                    description="the collection name to get records from",
                ),
            ],
            condition_tree: Annotated[
                Optional[Union[LeafComponents, BranchComponents]],
                Field(
                    description="condition tree to filter in the collection. "
                    "You can also include field from belongsTo & hasOne relations, by prefixing the targeted field by the relation field name, separated with ':'"
                    "LLM should read this page before use: https://docs.forestadmin.com/developer-guide-agents-python/data-sources/getting-started/queries/filters",
                    default=None,
                ),
            ],
            search: Annotated[
                Optional[str],
                Field(
                    description="a text to search over searchable fields. Use None to not search",
                    default=None,
                ),
            ],
            search_extended: Annotated[
                Optional[bool],
                Field(
                    description="when a {search} is given, set this parameter to true to search over relations, "
                    "otherwise it will just search in collection columns",
                    default=None,
                ),
            ],
            segment: Annotated[
                Optional[str],
                Field(
                    description="List of available segment can be obtain with tool collection-segments."
                    "LLM should read this page before use: https://docs.forestadmin.com/developer-guide-agents-python/agent-customization/segments.",
                    default=None,
                ),
            ],
            projection: Annotated[
                Optional[List[str]],
                Field(
                    description="The list of field to return for each record. "
                    "If set to None, all fields will be used. "
                    "You can also include field from belongsTo & hasOne relations, by prefixing the targeted field by the relation field name, separated with ':'"
                    "LLM should read this page before use: https://docs.forestadmin.com/documentation/reference-guide/fields/projections.",
                    default=None,
                ),
            ],
            page: Annotated[PlainPage, Field(description="pagination")],
            # context: Context,
        ) -> List[Dict[str, Any]]:
            """list records of {collection_name}. collection_name can be found using get_collections tool"""
            try:
                ForestLogger.log(
                    "info",
                    f"-- TOOL get_list of {collection_name}, \n"
                    f"projection: {projection}, condition_tree: {condition_tree}, segment: {segment}",
                )
                # total_wait = 30  # sec
                # nb_progress_report = 20
                # for i in range(nb_progress_report):
                #     await context.report_progress(i / nb_progress_report, nb_progress_report)
                #     time.sleep(total_wait / nb_progress_report)
                collection = self.datasource.get_collection(collection_name)
                filter_ = PaginatedFilter({})
                if segment:
                    filter_.segment = segment
                if condition_tree:
                    parsed_condition_tree = ConditionTreeFactory.from_plain_object(condition_tree)
                    ProjectionValidator.validate(collection, parsed_condition_tree.projection)
                    filter_ = filter_.override({"condition_tree": parsed_condition_tree})

                if search and len(search) > 0:
                    filter_ = filter_.override({"search": search, "search_extended": search_extended or False})

                if projection:
                    ProjectionValidator.validate(collection, projection)

            except Exception as exc:
                return str(exc)

            try:
                ret = await collection.list(
                    None,
                    filter_,
                    (Projection(*projection) if projection else ProjectionFactory.all(collection)),
                )
                ForestLogger.log("info", f"-- TOOL get_list of {collection_name} ; {len(ret)} records")
                return ret
            except Exception as exc:
                ForestLogger.log("exception", f"mcp execute error {exc}")
                return str(exc)
