from typing import Dict, Set, Tuple

from django.contrib.postgres import fields as postgres_fields
from django.db import models
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType


class ConverterException(DjangoDatasourceException):
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

        if isinstance(field, models.ForeignKey):
            return cls.convert(field.target_field)

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

    OPERATORS = {
        # TODO: add sensitive / insensitive case operators
        # operator:  (lookup_expr, negate needed)
        Operator.EQUAL: ("", False),
        Operator.NOT_EQUAL: ("", True),
        Operator.BLANK: ("__isnull", False),
        Operator.CONTAINS: ("__contains", False),
        Operator.NOT_CONTAINS: ("__icontains", True),
        Operator.STARTS_WITH: ("__istartswith", False),
        Operator.ENDS_WITH: ("__iendswith", False),
        Operator.GREATER_THAN: ("__gt", False),
        Operator.AFTER: ("__gt", False),
        Operator.LESS_THAN: ("__lt", False),
        Operator.BEFORE: ("__lt", False),
        Operator.MISSING: ("__isnull", False),
        Operator.PRESENT: ("__isnull", True),
        Operator.IN: ("__in", False),
        Operator.NOT_IN: ("__in", True),
        Operator.INCLUDES_ALL: ("__contains", False),
        Operator.MATCH: ("regex", False),
    }

    @classmethod
    def get_operator(cls, operator: Operator) -> Tuple[str, bool]:
        """return (expression_lookup, negate)"""
        try:
            return cls.OPERATORS[operator]
        except KeyError:
            raise ConverterException(f"Unable to handle the operator {operator}")

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
