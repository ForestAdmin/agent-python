from typing import Any, Dict, List

from aiohttp import ClientSession
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from typing_extensions import Self


class TypicodeCollection(Collection):
    def __init__(self, name: str, datasource: Datasource[Self]):
        super().__init__(name, datasource)
        self.enable_count()
        self.enable_search()

    def _build_request(self, filter_: Filter) -> Dict[str, Any]:
        request_params: Dict[str, Any] = {"url": f"https://jsonplaceholder.typicode.com/{self.name}s", "params": []}

        if filter_ and filter_.condition_tree:
            # Warning: this implementation ignores Or/And
            # It assumes that leafs targeting the same field are "or", and leaf targeting different
            # fields are "and", which is good enough for the same of example.
            query = {}

            def param_builder(leaf: ConditionTreeLeaf):
                if leaf.field in query and isinstance(query[leaf.field], list):
                    query[leaf.field].append(leaf.value)
                elif leaf.field in query:
                    query[leaf.field] = [query[leaf.field], leaf.value]
                else:
                    query[leaf.field] = leaf.value

            filter_.condition_tree.for_each_leaf(param_builder)
            request_params["params"].extend([(field, value) for field, value in query.items()])

        if filter_ and filter_.search:
            request_params["params"].append(("q", filter_.search))
        return request_params

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[Dict[str, Any]]:
        request = self._build_request(filter_.to_base_filter())
        if filter_ and filter_.page:
            request["params"].append(("_start", filter_.page.skip))
            request["params"].append(("_limit", filter_.page.limit))

        if filter_ and filter_.sort:
            request["params"].append(("_sort", ",".join([s["field"].replace(":", ".") for s in filter_.sort])))
            request["params"].append(("_order", ",".join(["asc" if s["ascending"] else "desc" for s in filter_.sort])))

        async with ClientSession() as session:
            async with session.get(**request) as response:
                response.raise_for_status()
                return await response.json()

    async def aggregate(
        self, caller: User, filter_: Filter | None, aggregation: Aggregation, limit: int | None = None
    ) -> List[AggregateResult]:
        # if aggregation.operation.value == "Count" and len(aggregation.groups) == 0:
        #     # there is no 'x-total-count' header anymore
        #     request = self._build_request(filter_)
        #     async with ClientSession() as session:
        #         async with session.get(**request) as response:
        #             response.raise_for_status()
        #             return [{"value": int(response.headers.get("x-total-count")), "group": {}}]

        return aggregation.apply(
            await self.list(caller, PaginatedFilter.from_base_filter(filter_), aggregation.projection),
            str(caller.timezone),
            limit,
        )


class Comments(TypicodeCollection):
    def __init__(self, datasource: Datasource[Self]):
        super().__init__("comment", datasource)

        self.add_fields(
            {
                "id": {
                    "type": "Column",
                    "is_primary_key": True,
                    "column_type": "Number",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "postId": {
                    "type": FieldType.COLUMN,
                    "column_type": "Number",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "name": {
                    "type": FieldType.COLUMN,
                    "column_type": "String",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "email": {
                    "type": FieldType.COLUMN,
                    "column_type": "String",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "body": {
                    "type": FieldType.COLUMN,
                    "column_type": "String",
                    "filter_operators": set([Operator.EQUAL]),
                },
            }
        )


class Post(TypicodeCollection):
    def __init__(self, datasource: Datasource[Self]):
        super().__init__("post", datasource)

        self.add_fields(
            {
                "id": {
                    "type": FieldType.COLUMN,
                    "is_primary_key": True,
                    "column_type": "Number",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "userId": {
                    "type": FieldType.COLUMN,
                    "column_type": "Number",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "title": {
                    "type": FieldType.COLUMN,
                    "column_type": "String",
                    "filter_operators": set([Operator.EQUAL]),
                },
                "body": {
                    "type": FieldType.COLUMN,
                    "column_type": "String",
                    "filter_operators": set([Operator.EQUAL]),
                },
            }
        )


class TypicodeDatasource(Datasource):
    def __init__(self) -> None:
        super().__init__()
        self.add_collection(Comments(self))
        self.add_collection(Post(self))
