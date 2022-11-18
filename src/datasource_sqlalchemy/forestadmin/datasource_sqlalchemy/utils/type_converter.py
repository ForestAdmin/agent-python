from typing import Any, Callable, Dict, Optional, Set, Type

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType
from sqlalchemy import ARRAY  # type: ignore
from sqlalchemy import column as SqlAlchemyColumn  # type: ignore
from sqlalchemy import func, not_, or_  # type: ignore
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import UUID


class ConverterException(DatasourceToolkitException):
    pass


class Converter:

    TYPES: Dict[Type[sqltypes.TypeEngine], PrimitiveType] = {
        sqltypes.BigInteger: PrimitiveType.NUMBER,
        sqltypes.Boolean: PrimitiveType.BOOLEAN,
        sqltypes.CHAR: PrimitiveType.STRING,
        sqltypes.Date: PrimitiveType.DATE_ONLY,
        sqltypes.DateTime: PrimitiveType.DATE,
        sqltypes.DECIMAL: PrimitiveType.NUMBER,
        sqltypes.Enum: PrimitiveType.ENUM,
        sqltypes.Float: PrimitiveType.NUMBER,
        sqltypes.Integer: PrimitiveType.NUMBER,
        sqltypes.JSON: PrimitiveType.JSON,
        sqltypes.Numeric: PrimitiveType.NUMBER,
        sqltypes.REAL: PrimitiveType.NUMBER,
        sqltypes.SmallInteger: PrimitiveType.NUMBER,
        sqltypes.String: PrimitiveType.STRING,
        sqltypes.Text: PrimitiveType.STRING,
        sqltypes.Time: PrimitiveType.TIME_ONLY,
        sqltypes.Unicode: PrimitiveType.STRING,
        sqltypes.UnicodeText: PrimitiveType.STRING,
        UUID: PrimitiveType.UUID,
    }

    @classmethod
    def convert(cls, _type: sqltypes.TypeEngine) -> ColumnAlias:
        type_class = _type.__class__
        if type_class == ARRAY:
            return [cls.convert(_type.item_type)]  # type: ignore
        try:
            return cls.TYPES[_type.__class__]
        except KeyError:
            raise ConverterException(f'Type "{_type.__class__}" is unknown')


class FilterOperator:

    COMMON_OPERATORS: Set[Operator] = {
        Operator.BLANK,
        Operator.EQUAL,
        Operator.MISSING,
        Operator.NOT_EQUAL,
        Operator.PRESENT,
    }

    OPERATORS = {
        Operator.EQUAL: "_equal_operator",
        Operator.NOT_EQUAL: "_not_equal_operator",
        Operator.BLANK: "_blank_operator",
        Operator.CONTAINS: "_contains_operator",
        Operator.NOT_CONTAINS: "_not_contains_operator",
        Operator.STARTS_WITH: "_starts_with_operator",
        Operator.ENDS_WITH: "_ends_with_operator",
        Operator.GREATER_THAN: "_greater_than_operator",
        Operator.LESS_THAN: "_less_than_operator",
        Operator.MISSING: "_missing_operator",
        Operator.PRESENT: "_present_operator",
        Operator.IN: "_in_operator",
        Operator.NOT_IN: "_not_in_operator",
        Operator.INCLUDES_ALL: "_includes_all",
    }

    @staticmethod
    def _equal_operator(column: SqlAlchemyColumn):
        return column.__eq__

    @staticmethod
    def _not_equal_operator(column: SqlAlchemyColumn):
        return column.__ne__

    @staticmethod
    def _blank_operator(column: SqlAlchemyColumn):
        def wrapped(_: str):
            return or_([column.is_(None), column.__eq__("")])

        return wrapped

    @staticmethod
    def _contains_operator(column: SqlAlchemyColumn):
        def wrapped(value: str):
            return func.lower(column).contains(value.lower())

        return wrapped

    @classmethod
    def _not_contains_operator(cls, column: SqlAlchemyColumn):
        def wrapped(value: str) -> Any:
            return not_(cls._contains_operator(column)(value))  # type: ignore

        return wrapped

    @staticmethod
    def _starts_with_operator(column: SqlAlchemyColumn):
        return column.startswith

    @staticmethod
    def _ends_with_operator(column: SqlAlchemyColumn):
        return column.endswith

    @staticmethod
    def _greater_than_operator(column: SqlAlchemyColumn):
        return column.__gt__

    @staticmethod
    def _less_than_operator(column: SqlAlchemyColumn):
        return column.__lt__

    @staticmethod
    def _in_operator(column: SqlAlchemyColumn):
        return column.in_

    @staticmethod
    def _not_in_operator(column: SqlAlchemyColumn):
        return column.not_in

    @staticmethod
    def _missing_operator(column: SqlAlchemyColumn):
        def wrapped(_: str):
            return column.is_(None)

        return wrapped

    @staticmethod
    def _present_operator(column: SqlAlchemyColumn):
        def wrapped(_: str):
            return column.is_not(None)

        return wrapped

    @staticmethod
    def _includes_all(column: SqlAlchemyColumn):
        return column.__eq__

    @classmethod
    def get_operator(cls, columns: SqlAlchemyColumn, operator: Operator) -> Callable[[Optional[str]], Any]:
        try:
            meth = cls.OPERATORS[operator]
        except KeyError:
            raise ConverterException(f"Unable to handle the operator {operator}")
        else:
            return getattr(cls, meth)(columns[0])

    @classmethod
    def get_for_type(cls, _type: ColumnAlias) -> set[Operator]:

        operators: Set[Operator] = set()
        if isinstance(_type, list):
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.IN,
                Operator.INCLUDES_ALL,
                Operator.NOT_IN,
            }
        elif _type == PrimitiveType.BOOLEAN:
            operators = cls.COMMON_OPERATORS
        elif _type == PrimitiveType.UUID:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.CONTAINS,
                Operator.ENDS_WITH,
                Operator.LIKE,
                Operator.STARTS_WITH,
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
            operators = {*cls.COMMON_OPERATORS, Operator.IN, Operator.NOT_IN}
        elif _type == PrimitiveType.JSON:
            operators = cls.COMMON_OPERATORS

        return operators
