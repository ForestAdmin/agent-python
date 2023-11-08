from typing import Dict, Set

from django.contrib.postgres import fields as postgres_fields
from django.db import models
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType


class ConverterException(DatasourceToolkitException):
    pass


class TypeConverter:
    TYPES: Dict[type, PrimitiveType] = {
        # string
        models.CharField: PrimitiveType.STRING,
        models.TextField: PrimitiveType.STRING,
        #
        # number
        models.IntegerField: PrimitiveType.NUMBER,
        models.FloatField: PrimitiveType.NUMBER,
        models.DecimalField: PrimitiveType.NUMBER,
        #
        # bool
        models.BooleanField: PrimitiveType.BOOLEAN,
        #
        # datetime
        # DateTimeField should be in first because it overrides DateField
        models.DateTimeField: PrimitiveType.DATE,
        models.DateField: PrimitiveType.DATE_ONLY,
        models.TimeField: PrimitiveType.TIME_ONLY,
        # https://docs.djangoproject.com/en/4.2/ref/models/fields/#durationfield
        models.DurationField: PrimitiveType.NUMBER,
        #
        # binary
        models.BinaryField: PrimitiveType.BINARY,
        #
        # file field
        models.FileField: PrimitiveType.STRING,
        models.FilePathField: PrimitiveType.STRING,
        #
        # ip address
        models.IPAddressField: PrimitiveType.STRING,
        models.GenericIPAddressField: PrimitiveType.STRING,
        #
        # json
        models.JSONField: PrimitiveType.JSON,
        #
        # uuid
        models.UUIDField: PrimitiveType.UUID,
        #
        # specific fields
        postgres_fields.CIText: PrimitiveType.STRING,
        postgres_fields.CIEmailField: PrimitiveType.STRING,
        postgres_fields.HStoreField: PrimitiveType.JSON,
        # postgres_fields.RangeField and subclassed ones not handles
    }

    @classmethod
    def convert(cls, field: models.Field) -> ColumnAlias:
        if field.choices is not None:
            return PrimitiveType.ENUM

        if field.__class__ in cls.TYPES:
            return cls.TYPES[field.__class__]

        if isinstance(field, postgres_fields.ArrayField):
            return [cls.convert(field.base_field)]

        for model_type, primitive_type in cls.TYPES.items():
            if isinstance(field, model_type):
                return primitive_type

        raise ConverterException(f'Type "{field.__class__}" is unknown')


class FilterOperator:
    COMMON_OPERATORS: Set[Operator] = {  # duplicated
        Operator.BLANK,
        Operator.EQUAL,
        Operator.MISSING,
        Operator.NOT_EQUAL,
        Operator.PRESENT,
    }

    # OPERATORS = {
    #     Operator.EQUAL: "_equal_operator",
    #     Operator.NOT_EQUAL: "_not_equal_operator",
    #     Operator.BLANK: "_blank_operator",
    #     Operator.CONTAINS: "_contains_operator",
    #     Operator.NOT_CONTAINS: "_not_contains_operator",
    #     Operator.STARTS_WITH: "_starts_with_operator",
    #     Operator.ENDS_WITH: "_ends_with_operator",
    #     Operator.GREATER_THAN: "_greater_than_operator",
    #     Operator.AFTER: "_greater_than_operator",
    #     Operator.LESS_THAN: "_less_than_operator",
    #     Operator.BEFORE: "_less_than_operator",
    #     Operator.MISSING: "_missing_operator",
    #     Operator.PRESENT: "_present_operator",
    #     Operator.IN: "_in_operator",
    #     Operator.NOT_IN: "_not_in_operator",
    #     Operator.INCLUDES_ALL: "_includes_all",
    #     Operator.MATCH: "_regexp_match",
    # }

    #     @staticmethod
    #     def _equal_operator(column: SqlAlchemyColumn):
    #         return column.__eq__

    #     @staticmethod
    #     def _not_equal_operator(column: SqlAlchemyColumn):
    #         return column.__ne__

    #     @staticmethod
    #     def _blank_operator(column: SqlAlchemyColumn):
    #         def wrapped(_: str):
    #             return or_([column.is_(None), column.__eq__("")])

    #         return wrapped

    #     @staticmethod
    #     def _contains_operator(column: SqlAlchemyColumn):
    #         def wrapped(value: str):
    #             return func.lower(column).contains(value.lower())

    #         return wrapped

    #     @classmethod
    #     def _not_contains_operator(cls, column: SqlAlchemyColumn):
    #         def wrapped(value: str) -> Any:
    #             return not_(cls._contains_operator(column)(value))  # type: ignore

    #         return wrapped

    #     @staticmethod
    #     def _starts_with_operator(column: SqlAlchemyColumn):
    #         return column.startswith

    #     @staticmethod
    #     def _ends_with_operator(column: SqlAlchemyColumn):
    #         return column.endswith

    #     @staticmethod
    #     def _greater_than_operator(column: SqlAlchemyColumn):
    #         return column.__gt__

    #     @staticmethod
    #     def _less_than_operator(column: SqlAlchemyColumn):
    #         return column.__lt__

    #     @staticmethod
    #     def _in_operator(column: SqlAlchemyColumn):
    #         return column.in_

    #     @staticmethod
    #     def _not_in_operator(column: SqlAlchemyColumn):
    #         return column.not_in

    #     @staticmethod
    #     def _missing_operator(column: SqlAlchemyColumn):
    #         def wrapped(_: str):
    #             return column.is_(None)

    #         return wrapped

    #     @staticmethod
    #     def _present_operator(column: SqlAlchemyColumn):
    #         def wrapped(_: str):
    #             return column.is_not(None)

    #         return wrapped

    #     @staticmethod
    #     def _includes_all(column: SqlAlchemyColumn):
    #         return column.__eq__

    #     @staticmethod
    #     def _regexp_match(column: SqlAlchemyColumn):
    #         return column.regexp_match

    #     @classmethod
    #     def get_operator(cls, columns: SqlAlchemyColumn, operator: Operator) -> Callable[[Optional[str]], Any]:
    #         try:
    #             meth = cls.OPERATORS[operator]
    #         except KeyError:
    #             raise ConverterException(f"Unable to handle the operator {operator}")
    #         else:
    #             return getattr(cls, meth)(columns[0])

    @classmethod
    def get_for_type(cls, _type: ColumnAlias) -> Set[Operator]:  # duplicated
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
        elif _type == PrimitiveType.BINARY:
            operators = {
                *cls.COMMON_OPERATORS,
                Operator.IN,
            }

        return operators
