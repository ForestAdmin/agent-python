from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict

from forestadmin.agent_toolkit.utils.context_variable_injector import ContextVariableInjector
from forestadmin.agent_toolkit.utils.context_variable_instantiator import ContextVariablesInstantiator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf

if TYPE_CHECKING:
    from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
    from forestadmin.agent_toolkit.utils.context import Request


class ContextVariableInjectorResourceMixin:
    async def inject_context_variables_in_filter(self, request: "RequestCollection"):
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

    async def inject_and_get_context_variables_in_live_query_segment(
        self, request: "RequestCollection"
    ) -> Dict[str, str]:
        context_variables_dct = request.query.pop("contextVariables", {})

        context_variables = await ContextVariablesInstantiator.build_context_variables(
            request.user, context_variables_dct, self.permission
        )

        request.query["segmentQuery"], vars = ContextVariableInjector.format_query_and_get_vars(
            request.query["segmentQuery"], context_variables
        )
        return vars

    async def inject_and_get_context_variables_in_live_query_chart(self, request: "Request") -> Dict[str, str]:
        context_variables_dct = request.body.get("contextVariables", {})
        context_variables = await ContextVariablesInstantiator.build_context_variables(
            request.user, context_variables_dct, self.permission
        )

        request.body["query"], vars = ContextVariableInjector.format_query_and_get_vars(
            request.body["query"], context_variables
        )
        return vars
