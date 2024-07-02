from typing import Any, Callable, Dict, Optional, Type

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType
from forestadmin.datasource_toolkit.utils.operators import BaseFilterOperator
from sqlalchemy import ARRAY  # type: ignore
from sqlalchemy import column as SqlAlchemyColumn  # type: ignore
from sqlalchemy import func, not_, or_  # type: ignore
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import UUID


class ConverterException(DatasourceToolkitException):
    pass


_UUID_TYPES = {
    UUID: PrimitiveType.UUID,
}
if getattr(sqltypes, "Uuid", None):
    _UUID_TYPES[sqltypes.Uuid] = PrimitiveType.UUID
    _UUID_TYPES[sqltypes.UUID] = PrimitiveType.UUID


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
        sqltypes.LargeBinary: PrimitiveType.BINARY,
        sqltypes.BINARY: PrimitiveType.BINARY,
        sqltypes.PickleType: PrimitiveType.BINARY,
        **_UUID_TYPES,
    }

    @classmethod
    def convert(cls, _type: sqltypes.TypeEngine) -> ColumnAlias:
        type_class = _type.__class__
        if type_class == ARRAY:
            return [cls.convert(_type.item_type)]  # type: ignore
        try:
            if type_class in cls.TYPES:
                return cls.TYPES[type_class]
            elif isinstance(_type, sqltypes.TypeDecorator):  # custom type
                return cls.convert(_type.impl)
            else:
                raise ConverterException(f'Type "{_type.__class__}" is unknown')
        except KeyError:
            raise ConverterException(f'Type "{_type.__class__}" is unknown')


class FilterOperator(BaseFilterOperator):
    OPERATORS = {
        Operator.EQUAL: "_equal_operator",
        Operator.NOT_EQUAL: "_not_equal_operator",
        Operator.BLANK: "_blank_operator",
        Operator.CONTAINS: "_contains_operator",
        Operator.NOT_CONTAINS: "_not_contains_operator",
        Operator.STARTS_WITH: "_starts_with_operator",
        Operator.ENDS_WITH: "_ends_with_operator",
        Operator.GREATER_THAN: "_greater_than_operator",
        Operator.AFTER: "_greater_than_operator",
        Operator.LESS_THAN: "_less_than_operator",
        Operator.BEFORE: "_less_than_operator",
        Operator.MISSING: "_missing_operator",
        Operator.PRESENT: "_present_operator",
        Operator.IN: "_in_operator",
        Operator.NOT_IN: "_not_in_operator",
        Operator.INCLUDES_ALL: "_includes_all",
        Operator.MATCH: "_regexp_match",
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
        # TODO: this is false, include is more what we want
        return column.__eq__

    @staticmethod
    def _regexp_match(column: SqlAlchemyColumn):
        return column.regexp_match

    @classmethod
    def get_operator(cls, columns: SqlAlchemyColumn, operator: Operator) -> Callable[[Optional[str]], Any]:
        try:
            meth = cls.OPERATORS[operator]
        except KeyError:
            raise ConverterException(f"Unable to handle the operator {operator}")
        else:
            return getattr(cls, meth)(columns[0])
