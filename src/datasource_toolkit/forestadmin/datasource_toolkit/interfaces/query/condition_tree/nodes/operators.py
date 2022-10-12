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
