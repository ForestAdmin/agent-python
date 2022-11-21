# This set of operators is enough to implement them all with replacements

from forestadmin.datasource_toolkit.interfaces.fields import Operator

UNIQUE_OPERATORS = {
    # All types besides arrays
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.LESS_THAN,
    Operator.GREATER_THAN,
    # Strings
    Operator.LIKE,
    Operator.NOT_CONTAINS,
    Operator.LONGER_THAN,
    Operator.SHORTER_THAN,
    # Arrays
    Operator.INCLUDES_ALL,
}

INTERVAL_OPERATORS = {
    Operator.TODAY,
    Operator.YESTERDAY,
    Operator.PREVIOUS_MONTH,
    Operator.PREVIOUS_QUARTER,
    Operator.PREVIOUS_WEEK,
    Operator.PREVIOUS_YEAR,
    Operator.PREVIOUS_MONTH_TO_DATE,
    Operator.PREVIOUS_QUARTER_TO_DATE,
    Operator.PREVIOUS_WEEK_TO_DATE,
    Operator.PREVIOUS_YEAR_TO_DATE,
    Operator.PREVIOUS_X_DAYS,
    Operator.PREVIOUS_X_DAYS_TO_DATE,
}

OTHER_OPERATORS = {
    Operator.PRESENT,
    Operator.BLANK,
    Operator.MISSING,
    Operator.IN,
    Operator.NOT_IN,
    Operator.STARTS_WITH,
    Operator.ENDS_WITH,
    Operator.CONTAINS,
    Operator.BEFORE,
    Operator.AFTER,
    Operator.AFTER_X_HOURS_AGO,
    Operator.BEFORE_X_HOURS_AGO,
    Operator.FUTURE,
    Operator.PAST,
}

ALL_OPERATORS = {*UNIQUE_OPERATORS, *INTERVAL_OPERATORS, *OTHER_OPERATORS}
