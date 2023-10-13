from typing import List, Optional, Set

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType


class FrontendFilterableUtils:
    BASE_OPERATORS = [Operator.EQUAL, Operator.NOT_EQUAL, Operator.PRESENT, Operator.BLANK]

    DATE_OPERATORS = [
        Operator.LESS_THAN,
        Operator.GREATER_THAN,
        Operator.TODAY,
        Operator.YESTERDAY,
        Operator.PREVIOUS_X_DAYS,
        Operator.PREVIOUS_WEEK,
        Operator.PREVIOUS_QUARTER,
        Operator.PREVIOUS_MONTH,
        Operator.PREVIOUS_YEAR,
        Operator.PREVIOUS_X_DAYS_TO_DATE,
        Operator.PREVIOUS_WEEK_TO_DATE,
        Operator.PREVIOUS_QUARTER_TO_DATE,
        Operator.PREVIOUS_MONTH_TO_DATE,
        Operator.PREVIOUS_YEAR_TO_DATE,
        Operator.PAST,
        Operator.FUTURE,
        Operator.BEFORE_X_HOURS_AGO,
        Operator.AFTER_X_HOURS_AGO,
    ]

    OPERATOR_BY_TYPES = {
        PrimitiveType.BOOLEAN: BASE_OPERATORS,
        PrimitiveType.ENUM: [*BASE_OPERATORS, Operator.IN],
        PrimitiveType.NUMBER: [*BASE_OPERATORS, Operator.IN, Operator.GREATER_THAN, Operator.LESS_THAN],
        PrimitiveType.STRING: [
            *BASE_OPERATORS,
            Operator.IN,
            Operator.STARTS_WITH,
            Operator.ENDS_WITH,
            Operator.CONTAINS,
            Operator.NOT_CONTAINS,
        ],
        PrimitiveType.UUID: BASE_OPERATORS,
        PrimitiveType.DATE: [*BASE_OPERATORS, *DATE_OPERATORS],
        PrimitiveType.DATE_ONLY: [*BASE_OPERATORS, *DATE_OPERATORS],
        PrimitiveType.TIME_ONLY: [*BASE_OPERATORS, *DATE_OPERATORS],
        PrimitiveType.BINARY: [*BASE_OPERATORS, Operator.IN],
    }

    @classmethod
    def is_filterable(cls, column_type: ColumnAlias, operators: Optional[Set[Operator]]) -> bool:
        required_operators = cls.get_required_operators(column_type) or []
        return bool(operators and all([op in operators for op in required_operators]))

    @classmethod
    def get_required_operators(cls, column_type: ColumnAlias) -> Optional[List[Operator]]:
        res = None
        if isinstance(column_type, PrimitiveType):
            res = cls.OPERATOR_BY_TYPES.get(column_type)
        elif isinstance(column_type, list):
            res = [Operator.INCLUDES_ALL]
        return res
