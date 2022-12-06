from typing import Any, List, Optional, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    PrimitiveType,
    is_column,
    is_many_to_one,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter
from forestadmin.datasource_toolkit.validations.types import ValidationPrimaryType, ValidationType, ValidationTypesArray


class FieldValidatorException(DatasourceToolkitException):
    pass


class FieldValidator:
    @classmethod
    def validate(cls, collection: Collection, field: str, values: Optional[List[Any]] = None) -> None:
        nested_field = None
        if ":" in field:
            field, *nested_field = field.split(":")
            nested_field = ":".join(nested_field)
        try:
            schema = collection.schema["fields"][field]
        except KeyError:
            raise DatasourceToolkitException(f"Column not found: {collection.name}.{field}")

        if not nested_field:
            if not is_column(schema):
                raise DatasourceToolkitException(
                    f'Unexpected field type: {collection.name}.{field} (found {schema["type"]} expected Column)'
                )
            if values is not None:
                for value in values:
                    cls.validate_value(field, schema, value)
        else:
            if not (is_many_to_one(schema) or is_one_to_one(schema)):
                raise FieldValidatorException(f'Unexpected field type {schema["type"]}: {collection.name}.{field}')

            association = collection.datasource.get_collection(schema["foreign_collection"])
            cls.validate(association, nested_field, values)

    @classmethod
    def validate_value(
        cls,
        field: str,
        schema: Column,
        value: Any,
        allowed_types: Optional[
            Union[List[Union[PrimitiveType, ValidationType]], List[Union[PrimitiveType, ValidationPrimaryType]]]
        ] = None,
    ):
        column_type = schema["column_type"]
        if not isinstance(column_type, PrimitiveType):
            return

        type = TypeGetter.get(value, column_type)

        if column_type == PrimitiveType.ENUM:
            cls.check_enum_value(type, schema, value)

        if allowed_types:
            if type not in allowed_types:
                raise FieldValidatorException(f'Wrong type for "{field}": {value}. Expects [{allowed_types}]')
        elif type != column_type:
            raise FieldValidatorException(f'Wrong type for "{field}": {value}. Expects {column_type}')

    @staticmethod
    def check_enum_value(type: Union[PrimitiveType, ValidationType], column_schema: Column, enum_value: Any):
        is_enum_allowed: bool = True

        if not column_schema["enum_values"]:
            raise FieldValidatorException("Missing enum_values")

        if type == ValidationTypesArray.ENUM:
            enum_values_condition_tree = cast(List[str], enum_value)
            if column_schema["enum_values"]:
                is_enum_allowed = all([value in column_schema["enum_values"] for value in enum_values_condition_tree])
        else:
            is_enum_allowed = enum_value in column_schema["enum_values"]
        if not is_enum_allowed:
            raise FieldValidatorException(
                f'The given enum value(s) [{enum_value}] is not listed in [{column_schema["enum_values"]}]'
            )
