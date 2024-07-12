from typing import Set

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType


class BaseFilterOperator:
    COMMON_OPERATORS: Set[Operator] = {
        Operator.BLANK,
        Operator.EQUAL,
        Operator.MISSING,
        Operator.NOT_EQUAL,
        Operator.PRESENT,
    }

    @classmethod
    def get_for_type(cls, _type: ColumnAlias) -> Set[Operator]:
        operators: Set[Operator] = set()
        if isinstance(_type, list):
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.IN,
                Operator.INCLUDES_ALL,
                Operator.NOT_IN,
            }
        elif _type == PrimitiveType.BOOLEAN:
            operators = {*cls.COMMON_OPERATORS}
        elif _type == PrimitiveType.UUID:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.CONTAINS,
                Operator.ENDS_WITH,
                Operator.LIKE,
                Operator.STARTS_WITH,
                Operator.IN,
                Operator.NOT_IN,
            }
        elif _type == PrimitiveType.NUMBER:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.GREATER_THAN,
                Operator.LESS_THAN,
                Operator.IN,
                Operator.NOT_IN,
            }
        elif _type == PrimitiveType.STRING:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.CONTAINS,
                Operator.ENDS_WITH,
                Operator.IN,
                Operator.LIKE,
                Operator.LONGER_THAN,
                Operator.NOT_CONTAINS,
                Operator.NOT_IN,
                Operator.SHORTER_THAN,
                Operator.STARTS_WITH,
            }
        elif _type in [
            PrimitiveType.DATE,
            PrimitiveType.DATE_ONLY,
            PrimitiveType.TIME_ONLY,
        ]:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.GREATER_THAN,
                Operator.LESS_THAN,
            }
        elif _type == PrimitiveType.ENUM:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.IN,
                Operator.NOT_IN,
            }
        elif _type == PrimitiveType.JSON:
            operators = {*cls.COMMON_OPERATORS}
        elif _type == PrimitiveType.BINARY:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.IN,
                Operator.NOT_IN,
            }

        return operators
