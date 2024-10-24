from typing import Set

from forestadmin.datasource_toolkit.interfaces.fields import Operator


class FrontendFilterableUtils:

    @classmethod
    def is_filterable(cls, operators: Set[Operator]) -> bool:
        return operators is not None and len(operators) > 0
