from datetime import date, datetime
from typing import Any, Dict, List, Literal, Union, cast
from uuid import uuid1

import pandas as pd
from forestadmin.agent_toolkit.resources.collections import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method
from forestadmin.agent_toolkit.resources.collections.filter import build_filter
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.utils.context import (
    FileResponse,
    Request,
    RequestMethod,
    Response,
    build_client_error_response,
    build_success_response,
)
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import Frequency
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class StatsResource(BaseCollectionResource):

    FREQUENCIES = {"Day": Frequency.DAY, "Week": Frequency.WEEK, "Month": Frequency.MONTH, "Year": Frequency.YEAR}

    FORMAT = {"Day": "%d/%m/%Y", "Week": "W%W-%Y", "Month": "%m %Y", "Year": "%Y"}

    def stats_method(self, type: str):
        return {
            "Value": self.value,
            "Objective": self.objective,
            "Pie": self.pie,
            "Line": self.line,
            "Leaderboard": self.leader_board,
        }[type]

    async def dispatch(self, request: Request, method_name: Literal["add"]) -> Union[Response, FileResponse]:
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            return build_client_error_response([str(e)])

        try:
            meth = self.stats_method(request_collection.body["type"])  # type: ignore
        except KeyError:
            return build_client_error_response(
                [f"Unknown stats type {request_collection.body.get('type')}"]  # type: ignore
            )
        except TypeError:
            return build_client_error_response(["Missing stats type in request body"])
        return await meth(request_collection)

    @check_method(RequestMethod.POST)
    @authenticate
    async def value(self, request: RequestCollection) -> Response:
        current_filter = await self._get_gilter(request)
        result = {
            "countCurrent": await self._compute_value(request, current_filter),
        }

        if current_filter.condition_tree:
            current_filter.condition_tree = cast(ConditionTreeBranch, current_filter.condition_tree)
            with_count_previous = self._with_count_previous(current_filter.condition_tree)
            if (
                not hasattr(current_filter.condition_tree, "aggregator")
                or not current_filter.condition_tree.aggregator != Aggregator.AND
            ) and with_count_previous:
                result["countPrevious"] = await self._compute_value(
                    request, FilterFactory.get_previous_period_filter(current_filter)
                )

        return self._build_success_response(result)

    @check_method(RequestMethod.POST)
    @authenticate
    async def objective(self, request: RequestCollection) -> Response:
        current_filter = await self._get_gilter(request)
        result = {"value": await self._compute_value(request, current_filter)}
        return self._build_success_response(result)

    @check_method(RequestMethod.POST)
    @authenticate
    async def pie(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception

        current_filter = await self._get_gilter(request)
        aggregation = Aggregation(
            {
                "operation": request.body["aggregate"],
                "field": request.body.get("aggregate_field"),
                "groups": [{"field": request.body["group_by_field"]}],
            }
        )
        rows = await request.collection.aggregate(current_filter, aggregation)
        results: List[Dict[str, Union[str, int]]] = []
        for row in rows:
            key = row["group"][request.body["group_by_field"]]
            field = request.collection.get_field(request.body["group_by_field"])
            if cast(Column, field)["column_type"] == PrimitiveType.ENUM:
                key = key.value
            results.append({"key": key, "value": row["value"]})
        return self._build_success_response(results)

    @check_method(RequestMethod.POST)
    @authenticate
    async def line(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception

        current_filter = await self._get_gilter(request)
        aggregation = Aggregation(
            {
                "operation": request.body["aggregate"],
                "field": request.body.get("aggregate_field"),
                "groups": [{"field": request.body["group_by_date_field"], "operation": request.body["time_range"]}],
            }
        )
        rows = await request.collection.aggregate(current_filter, aggregation)
        values = {
            datetime.fromisoformat(row["group"][request.body["group_by_date_field"]]).date(): row["value"]
            for row in rows
            if row["group"][request.body["group_by_date_field"]] is not None
        }
        dates = list(values.keys())
        dates.sort()
        end = dates[-1]
        start = dates[0]
        datapoints: List[Dict[str, Union[date, Dict[str, int]]]] = []
        for dt in pd.date_range(  # type: ignore
            start=start, end=end, freq=self.FREQUENCIES[request.body["time_range"]].value
        ).to_pydatetime():
            datapoints.append(
                {
                    "label": dt.strftime(self.FORMAT[request.body["time_range"]]),
                    "values": {"value": values.get(dt.date(), 0)},
                }
            )
        return self._build_success_response(datapoints)

    @check_method(RequestMethod.POST)
    @authenticate
    async def leader_board(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception
        aggregate = request.body["aggregate"]
        label_field = request.body["label_field"]
        relationship_field = request.body["relationship_field"]
        limit = request.body["limit"]
        aggregate_field = request.body.get("aggregate_field")
        if not aggregate_field:
            relation = SchemaUtils.get_to_many_relation(request.collection.schema, relationship_field)
            foreign_collection = relation["foreign_collection"]
            collection = request.collection.datasource.get_collection(foreign_collection)
            pks = SchemaUtils.get_primary_keys(collection.schema)
            aggregate_field = pks[0]
        current_filter = await self._get_gilter(request)
        aggregation = Aggregation(
            {
                "operation": aggregate,
                "field": f"{relationship_field}:{aggregate_field}",
                "groups": [{"field": label_field}],
            }
        )

        rows = await request.collection.aggregate(current_filter, aggregation, int(limit))
        results: List[Dict[str, Union[str, int]]] = []
        for row in rows:
            results.append({"key": row["group"][label_field], "value": row["value"]})
        return self._build_success_response(results)

    def _build_success_response(self, result: Any) -> Response:
        return build_success_response({"data": {"id": uuid1().hex, "type": "stats", "attributes": {"value": result}}})

    def _with_count_previous(self, tree: ConditionTree):
        use_interval_res: List[bool] = []

        def _use_interval_res(tree: ConditionTree) -> None:
            if isinstance(tree, ConditionTreeLeaf):
                use_interval_res.append(tree.use_interval_operator)

        tree.apply(_use_interval_res)
        return any(use_interval_res)

    async def _get_gilter(self, request: RequestCollection) -> Filter:
        scope_tree = await self.permission.get_scope(request, request.collection)
        return build_filter(request, scope_tree)

    async def _compute_value(self, request: RequestCollection, filter: Filter) -> int:
        if not request.body:
            raise Exception
        aggregation = Aggregation(
            {"operation": request.body["aggregate"], "field": request.body.get("aggregate_field")}
        )
        rows = await request.collection.aggregate(filter, aggregation)
        res = 0
        if len(rows):
            res = int(rows[0]["value"])
        return res
