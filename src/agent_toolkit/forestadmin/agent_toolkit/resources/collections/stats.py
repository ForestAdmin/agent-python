import json
from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Union, cast
from uuid import uuid1

import pandas as pd
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.resources.collections.base_collection_resource import BaseCollectionResource
from forestadmin.agent_toolkit.resources.collections.decorators import (
    authenticate,
    authorize,
    check_method,
    ip_white_list,
)
from forestadmin.agent_toolkit.resources.collections.filter import build_filter
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestCollectionException
from forestadmin.agent_toolkit.utils.context import FileResponse, HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.agent_toolkit.utils.context_variable_injector import ContextVariableInjector
from forestadmin.agent_toolkit.utils.context_variable_instantiator import ContextVariablesInstantiator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class StatsResource(BaseCollectionResource):
    FREQUENCIES = {"Day": "d", "Week": "W-MON", "Month": "BMS", "Year": "BYS"}

    FORMAT = {"Day": "%d/%m/%Y", "Week": "W%V-%Y", "Month": "%b %Y", "Year": "%Y"}

    def stats_method(self, type: str):
        return {
            "Value": self.value,
            "Objective": self.objective,
            "Pie": self.pie,
            "Line": self.line,
            "Leaderboard": self.leader_board,
        }[type]

    @ip_white_list
    async def dispatch(
        self, request: Request, method_name: Optional[Literal["add"]] = None
    ) -> Union[Response, FileResponse]:
        try:
            request_collection = RequestCollection.from_request(request, self.datasource)
        except RequestCollectionException as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

        try:
            meth = self.stats_method(request_collection.body["type"])  # type: ignore
        except KeyError:
            ForestLogger.log("exception", f"Unknown stats type {request_collection.body.get('type')}")
            return HttpResponseBuilder.build_client_error_response(
                [ForestException(f"Unknown stats type {request_collection.body.get('type')}")]  # type: ignore
            )
        except TypeError:
            ForestLogger.log("exception", "Missing stats type in request body")
            return HttpResponseBuilder.build_client_error_response(
                [ForestException("Missing stats type in request body")]
            )
        try:
            return await meth(request_collection)
        except Exception as exc:
            ForestLogger.log("exception", exc)
            return HttpResponseBuilder.build_client_error_response([exc])

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("chart")
    async def value(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception
        current_filter = await self._get_filter(request)
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
    @authorize("chart")
    async def objective(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception
        current_filter = await self._get_filter(request)
        result = {"value": await self._compute_value(request, current_filter)}
        return self._build_success_response(result)

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("chart")
    async def pie(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception

        current_filter = await self._get_filter(request)
        aggregation = Aggregation(
            {
                "operation": request.body["aggregator"],
                "field": request.body.get("aggregateFieldName"),
                "groups": [{"field": request.body["groupByFieldName"]}],
            }
        )
        rows = await request.collection.aggregate(request.user, current_filter, aggregation)
        results: List[Dict[str, Union[str, int]]] = []
        for row in rows:
            key = row["group"][request.body["groupByFieldName"]]
            results.append({"key": key, "value": row["value"]})
        return self._build_success_response(results)

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("chart")
    async def line(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception
        for key in ["timeRange", "groupByFieldName", "aggregator"]:
            if key not in request.body:
                raise ForestException(f"The parameter {key} is not defined")

        current_filter = await self._get_filter(request)
        aggregation = Aggregation(
            {
                "operation": request.body["aggregator"],
                "field": request.body.get("aggregateFieldName"),
                "groups": [{"field": request.body["groupByFieldName"], "operation": request.body["timeRange"]}],
            }
        )
        rows = await request.collection.aggregate(request.user, current_filter, aggregation)
        dates = []
        values_label = {}
        for row in rows:
            label = row["group"][request.body["groupByFieldName"]]
            if label is not None:
                if isinstance(label, str):
                    label = datetime.fromisoformat(label).date()
                elif isinstance(label, datetime):
                    label = label.date()
                elif isinstance(label, date):
                    pass
                else:
                    ForestLogger.log(
                        "warning",
                        f"The time chart label type must be 'str' or 'date', not {type(label)}. Skipping this record.",
                    )
                dates.append(label)
                values_label[label.strftime(self.FORMAT[request.body["timeRange"]])] = row["value"]

        dates.sort()
        end = dates[-1]
        start = dates[0]
        data_points: List[Dict[str, Union[date, Dict[str, int]]]] = []
        for dt in pd.date_range(  # type: ignore
            start=start, end=end, freq=self.FREQUENCIES[request.body["timeRange"]]
        ).to_pydatetime():
            label = dt.strftime(self.FORMAT[request.body["timeRange"]])
            data_points.append(
                {
                    "label": label,
                    "values": {"value": values_label.get(label, 0)},
                }
            )
        return self._build_success_response(data_points)

    @check_method(RequestMethod.POST)
    @authenticate
    @authorize("chart")
    async def leader_board(self, request: RequestCollection) -> Response:
        if not request.body:
            raise Exception
        for key in ["aggregator", "labelFieldName", "relationshipFieldName"]:
            if key not in request.body:
                raise ForestException(f"The parameter {key} is not defined")

        aggregate = request.body["aggregator"]
        label_field = request.body["labelFieldName"]
        relationship_field = request.body["relationshipFieldName"]
        limit = request.body.get("limit")
        limit = int(limit) if isinstance(limit, str) else limit
        aggregate_field = request.body.get("aggregateFieldName")
        if not aggregate_field:
            relation = SchemaUtils.get_to_many_relation(request.collection.schema, relationship_field)
            foreign_collection = relation["foreign_collection"]
            collection = request.collection.datasource.get_collection(foreign_collection)
            pks = SchemaUtils.get_primary_keys(collection.schema)
            aggregate_field = pks[0]
        current_filter = await self._get_filter(request)
        aggregation = Aggregation(
            {
                "operation": aggregate,
                "field": f"{relationship_field}:{aggregate_field}",
                "groups": [{"field": label_field}],
            }
        )

        rows = await request.collection.aggregate(request.user, current_filter, aggregation, limit)
        results: List[Dict[str, Union[str, int]]] = []
        for row in rows:
            results.append({"key": row["group"][label_field], "value": row["value"]})
        return self._build_success_response(results)

    def _build_success_response(self, result: Any) -> Response:
        return HttpResponseBuilder.build_success_response(
            {"data": {"id": uuid1().hex, "type": "stats", "attributes": {"value": result}}}
        )

    def _with_count_previous(self, tree: ConditionTree):
        use_interval_res: List[bool] = []

        def _use_interval_res(tree: ConditionTree) -> None:
            if isinstance(tree, ConditionTreeLeaf):
                use_interval_res.append(tree.use_interval_operator)

        tree.apply(_use_interval_res)
        return any(use_interval_res)

    async def _get_filter(self, request: RequestCollection) -> Filter:
        scope_tree = await self.permission.get_scope(request.user, request.collection)
        await self.__inject_context_variables(request)
        return build_filter(request, scope_tree)

    async def _compute_value(self, request: RequestCollection, filter: Filter) -> int:
        aggregation = Aggregation(
            {"operation": request.body["aggregator"], "field": request.body.get("aggregateFieldName")}
        )
        rows = await request.collection.aggregate(request.user, filter, aggregation)
        res = 0
        if len(rows):
            res = int(rows[0]["value"])
        return res

    async def __inject_context_variables(self, request: RequestCollection):
        context_variables_dct = request.body.pop("contextVariables", {})
        if request.body.get("filter") is None:
            return

        context_variables = await ContextVariablesInstantiator.build_context_variables(
            request.user, context_variables_dct, self.permission
        )
        condition_tree = request.body["filter"]
        if isinstance(request.body["filter"], str):
            condition_tree = json.loads(condition_tree)

        condition_tree = ConditionTreeFactory.from_plain_object(condition_tree)

        injected_filter: ConditionTree = condition_tree.replace(
            lambda leaf: ConditionTreeLeaf(
                leaf.field,
                leaf.operator,
                ContextVariableInjector.inject_context_in_value(leaf.value, context_variables),
            )
        )

        request.body["filter"] = injected_filter.to_plain_object()
