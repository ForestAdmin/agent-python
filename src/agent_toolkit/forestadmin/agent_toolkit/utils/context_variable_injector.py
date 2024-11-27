import re
from typing import Dict, Optional, Tuple

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

    @staticmethod
    def format_query_and_get_vars(value: str, context_variable: ContextVariables) -> Tuple[str, Dict[str, str]]:
        if not isinstance(value, str):
            return value
        variables = {}
        # to allow datasources to rework variables:
        # - '%' are replaced by '\%'
        # - '{{var}}' are replaced by '%(var)s'
        # - '.' in vars are replaced by '__', and also in the returned mapping
        # - and the mapping of vars is returned

        def _match(match):
            variables[match.group(1).replace(".", "__")] = context_variable.get_value(match.group(1))
            return f"%({match.group(1).replace('.', '__')})s"

        ret = re.sub(r"{{([^}]+)}}", _match, value.replace("%", "\\%"))

        return (ret, variables)
