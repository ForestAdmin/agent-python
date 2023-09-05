import re
from typing import Optional

from forestadmin.agent_toolkit.utils.context_variables import ContextVariables
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch


class ContextVariableInjector:
    @staticmethod
    def inject_context_in_filter(filter_: Optional[ConditionTree], context_variable: ContextVariables):
        if filter_ is None:
            return None

        if isinstance(filter_, ConditionTreeBranch):  # or "conditions" in filter_
            return filter_.replace(
                lambda condition: ContextVariableInjector.inject_context_in_filter(condition, context_variable)
            )

        return filter_.replace(
            lambda leaf: leaf.override(
                {"value": ContextVariableInjector.inject_context_in_value(filter_.value, context_variable)}
            )
        )

    @staticmethod
    def inject_context_in_value(value, context_variable: ContextVariables):
        if not isinstance(value, str):
            return value

        return re.sub(r"{{([^}]+)}}", lambda match: str(context_variable.get_value(match.group(1))), value)
