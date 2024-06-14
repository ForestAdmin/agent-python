from collections import defaultdict
from typing import Any, Dict, List

from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.validations.types import ValidationPrimaryType, ValidationTypesArray

BASE_OPERATORS = [Operator.BLANK, Operator.EQUAL, Operator.MISSING, Operator.NOT_EQUAL, Operator.PRESENT]

ARRAY_OPERATORS = [Operator.IN, Operator.NOT_IN, Operator.INCLUDES_ALL]

BASE_DATE_ONLY_OPERATORS = [
    Operator.TODAY,
    Operator.YESTERDAY,
    Operator.PREVIOUS_X_DAYS,
    Operator.PREVIOUS_X_DAYS_TO_DATE,
    Operator.PREVIOUS_WEEK,
    Operator.PREVIOUS_WEEK_TO_DATE,
    Operator.PREVIOUS_MONTH,
    Operator.PREVIOUS_MONTH_TO_DATE,
    Operator.PREVIOUS_QUARTER,
    Operator.PREVIOUS_QUARTER_TO_DATE,
    Operator.PREVIOUS_YEAR,
    Operator.PREVIOUS_YEAR_TO_DATE,
    Operator.PAST,
    Operator.FUTURE,
    Operator.BEFORE,
    Operator.AFTER,
]

MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE: Dict[PrimitiveType, List[Operator]] = {
    PrimitiveType.STRING: [
        *BASE_OPERATORS,
        *ARRAY_OPERATORS,
        Operator.CONTAINS,
        Operator.NOT_CONTAINS,
        Operator.ENDS_WITH,
        Operator.STARTS_WITH,
        Operator.LONGER_THAN,
        Operator.SHORTER_THAN,
        Operator.LIKE,
    ],
    PrimitiveType.NUMBER: [*BASE_OPERATORS, *ARRAY_OPERATORS, Operator.GREATER_THAN, Operator.LESS_THAN],
    PrimitiveType.DATE_ONLY: [*BASE_OPERATORS, *BASE_DATE_ONLY_OPERATORS],
    PrimitiveType.DATE: [
        *BASE_OPERATORS,
        *BASE_DATE_ONLY_OPERATORS,
        Operator.BEFORE_X_HOURS_AGO,
        Operator.AFTER_X_HOURS_AGO,
    ],
    PrimitiveType.TIME_ONLY: [*BASE_OPERATORS, Operator.LESS_THAN, Operator.GREATER_THAN],
    PrimitiveType.ENUM: [*BASE_OPERATORS, *ARRAY_OPERATORS],
    PrimitiveType.JSON: [Operator.BLANK, Operator.MISSING, Operator.PRESENT],
    PrimitiveType.BOOLEAN: BASE_OPERATORS,
    PrimitiveType.POINT: BASE_OPERATORS,
    PrimitiveType.UUID: [*BASE_OPERATORS, *ARRAY_OPERATORS],
}

MAP_ALLOWED_TYPES_FOR_COLUMN_TYPE = {
    PrimitiveType.STRING: [PrimitiveType.STRING, ValidationTypesArray.STRING, ValidationPrimaryType.NULL],
    PrimitiveType.NUMBER: [PrimitiveType.NUMBER, ValidationTypesArray.NUMBER, ValidationPrimaryType.NULL],
    PrimitiveType.BOOLEAN: [PrimitiveType.BOOLEAN, ValidationTypesArray.BOOLEAN, ValidationPrimaryType.NULL],
    PrimitiveType.ENUM: [PrimitiveType.ENUM, ValidationTypesArray.ENUM, ValidationPrimaryType.NULL],
    PrimitiveType.DATE: [PrimitiveType.DATE, PrimitiveType.NUMBER, ValidationPrimaryType.NULL],
    PrimitiveType.DATE_ONLY: [PrimitiveType.DATE_ONLY, PrimitiveType.NUMBER, ValidationPrimaryType.NULL],
    PrimitiveType.JSON: [PrimitiveType.JSON, ValidationPrimaryType.NULL],
    PrimitiveType.POINT: [PrimitiveType.POINT, ValidationPrimaryType.NULL],
    PrimitiveType.TIME_ONLY: [PrimitiveType.TIME_ONLY, ValidationPrimaryType.NULL],
    PrimitiveType.UUID: [PrimitiveType.UUID, ValidationTypesArray.UUID, ValidationPrimaryType.NULL],
}


def _compute_allowed_types_for_operators() -> Dict[Operator, List[PrimitiveType]]:
    res: Dict[Operator, List[PrimitiveType]] = defaultdict(list)
    for type, operators in MAP_ALLOWED_OPERATORS_FOR_COLUMN_TYPE.items():
        for operator in operators:
            res[operator].append(type)
    return res


NO_TYPES_ALLOWED = [ValidationPrimaryType.NULL]

MAP_ALLOWED_TYPES_FOR_OPERATOR: Dict[Operator, Any] = {
    **_compute_allowed_types_for_operators(),
    Operator.IN: [v for v in ValidationTypesArray],
    Operator.NOT_IN: [v for v in ValidationTypesArray],
    Operator.INCLUDES_ALL: [v for v in ValidationTypesArray],
    Operator.BLANK: NO_TYPES_ALLOWED,
    Operator.MISSING: NO_TYPES_ALLOWED,
    Operator.PRESENT: NO_TYPES_ALLOWED,
    Operator.YESTERDAY: NO_TYPES_ALLOWED,
    Operator.TODAY: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_QUARTER: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_YEAR: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_MONTH: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_WEEK: NO_TYPES_ALLOWED,
    Operator.PAST: NO_TYPES_ALLOWED,
    Operator.FUTURE: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_WEEK_TO_DATE: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_MONTH_TO_DATE: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_QUARTER_TO_DATE: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_YEAR_TO_DATE: NO_TYPES_ALLOWED,
    Operator.PREVIOUS_X_DAYS_TO_DATE: [PrimitiveType.NUMBER],
    Operator.PREVIOUS_X_DAYS: [PrimitiveType.NUMBER],
    Operator.BEFORE_X_HOURS_AGO: [PrimitiveType.NUMBER],
    Operator.AFTER_X_HOURS_AGO: [PrimitiveType.NUMBER],
}
