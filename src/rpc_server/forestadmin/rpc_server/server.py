import json
from typing import Any, Dict, Optional
from xmlrpc.server import SimpleXMLRPCServer

from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.interfaces.models.collections import JsonCollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort


class RpcServer:

    METHODS = {
        "handshake": "handshake",
        "list": "list",
    }

    def __init__(self, datasource: SqlAlchemyDatasource, host: str = "localhost", port: int = 1234):
        self.datasource = datasource
        self.server: SimpleXMLRPCServer = SimpleXMLRPCServer((host, port))

    def _register_methods(self):
        for method, func in self.METHODS.items():
            self.server.register_function(getattr(self, func), method)

    def start(self):
        self._register_methods()
        self.server.serve_forever()

    def handshake(self):
        res = {}
        for collection in self.datasource.collections:
            res[collection.name] = JsonCollectionSchema.dumps(collection.schema)
        return json.dumps(res)

    async def list(self, str: str):
        body: Dict[str, Any] = json.loads(str)  # type: ignore
        filter: PaginatedFilter = self.filter_from_body(body["params"])
        collection = self.datasource.get_collection(body["collection"])
        return await collection.list(filter, Projection(body["params"]["projection"]))

    def filter_from_body(self, params: Dict[str, Any]) -> PaginatedFilter:
        condition_tree: Optional[ConditionTree] = None
        page: Optional[Page] = None
        sort: Sort = Sort(params.get("sort", []))

        if params.get("condition_tree"):
            condition_tree = ConditionTreeFactory.from_plain_object(params["condition_tree"])

        if params.get("page"):
            page = Page(params["page"]["int"], params["page"]["limit"])

        return PaginatedFilter(
            {
                "condition_tree": condition_tree,
                "page": page,
                "sort": sort,
                "search": params.get("search"),
                "search_extended": params.get("search_extended", False),
                "segment": params.get("segment", ""),
                "timezone": params.get("timezone", "utc"),
            }
        )
