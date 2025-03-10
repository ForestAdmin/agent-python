from typing import Dict, Set, Tuple

import django
from django.db import models
from forestadmin.datasource_django.exception import DjangoDatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias, Operator, PrimitiveType
from forestadmin.datasource_toolkit.utils.operators import BaseFilterOperator

try:
    # if postgres driver is installed
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None

try:
    # GeneratedField is available since django 5
    from django.db.models import GeneratedField
except ImportError:
    GeneratedField = None


class ConverterException(DjangoDatasourceException):
    pass


if postgres_fields is not None:
    POSTGRES_TYPE: Dict[type, PrimitiveType] = {
        # specific postgres fields
        postgres_fields.HStoreField: PrimitiveType.JSON,
        # postgres_fields.RangeField and subclassed ones not handles
    }
    if django.VERSION[0] < 5 or (django.VERSION[0] == 5 and django.VERSION[1] < 1):
        POSTGRES_TYPE[postgres_fields.CIText] = PrimitiveType.STRING
        POSTGRES_TYPE[postgres_fields.CIEmailField] = PrimitiveType.STRING
else:
    POSTGRES_TYPE: Dict[type, PrimitiveType] = {}


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
        **POSTGRES_TYPE,
    }

    @classmethod
    def convert(cls, field: models.Field) -> ColumnAlias:
        if field.choices is not None:
            return PrimitiveType.ENUM

        if isinstance(field, models.ForeignKey):
            return cls.convert(field.target_field)

        if GeneratedField is not None and isinstance(field, GeneratedField):
            return cls.convert(field.output_field)

        if field.__class__ in cls.TYPES:
            return cls.TYPES[field.__class__]

        if postgres_fields is not None and isinstance(field, postgres_fields.ArrayField):
            return [cls.convert(field.base_field)]

        for model_type, primitive_type in cls.TYPES.items():
            if isinstance(field, model_type):
                return primitive_type

        raise ConverterException(f'Type "{field.__class__}" is unknown')


class FilterOperator(BaseFilterOperator):
    OPERATORS = {
        # operator:  (lookup_expr, negate needed)
        Operator.EQUAL: ("__exact", False),
        Operator.NOT_EQUAL: ("__exact", True),
        Operator.CONTAINS: ("__icontains", False),
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
        Operator.MATCH: ("__regex", False),
    }

    @classmethod
    def get_operator(cls, operator: Operator) -> Tuple[str, bool]:
        """return (expression_lookup, negate)"""
        try:
            return cls.OPERATORS[operator]
        except KeyError:
            raise ConverterException(f"Unable to handle the operator {operator}")

    @classmethod
    def get_operators_for_field(cls, field: models.Field) -> Set[Operator]:
        _type = TypeConverter.convert(field)
        wanted_operators = cls.get_for_type(_type)
        lookup_names = field.get_lookups().keys()
        unavailable_operators = []
        for wanted_operator in wanted_operators:
            if cls.OPERATORS.get(wanted_operator, ("",))[0].replace("__", "") not in lookup_names:
                unavailable_operators.append(wanted_operator)

        return set([operator for operator in wanted_operators if operator not in unavailable_operators])
