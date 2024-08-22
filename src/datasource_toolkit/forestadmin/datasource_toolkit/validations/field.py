import re
from typing import Any, List, Optional, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    Operator,
    PrimitiveType,
    is_column,
    is_many_to_one,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter
from forestadmin.datasource_toolkit.validations.types import ValidationPrimaryType, ValidationType, ValidationTypesArray


class FieldValidatorException(DatasourceToolkitException):
    pass


class FieldValidator:
    @classmethod
    def validate(cls, collection: Collection, field_p: str, values: Optional[List[Any]] = None) -> None:
        nested_field = None
        if ":" in field_p:
            field, nested_field = field_p.split(":", 1)
        else:
            field = field_p[:]

        field_list = collection.schema["fields"].keys()
        if field not in field_list:
            raise DatasourceToolkitException(
                f"Column not found: {collection.name}.{field}. Fields in {collection.name} are {', '.join(field_list)}"
            )

        schema = collection.schema["fields"][field]

        if nested_field is None:
            if not is_column(schema):
                raise DatasourceToolkitException(
                    f'Unexpected field type: {collection.name}.{field} (found {schema["type"]} expected Column)'
                )
            if values is not None:
                for value in values:
                    cls.validate_value(field, schema, value)
        else:
            if is_polymorphic_many_to_one(schema):
                if nested_field != "*":
                    raise FieldValidatorException(
                        f"Unexpected nested field {nested_field} under generic relation: {collection.name}.{field}"
                    )

            elif not (
                is_many_to_one(schema)
                or is_one_to_one(schema)
                or is_polymorphic_one_to_one(schema)
                or is_polymorphic_one_to_many(schema)
            ):
                raise FieldValidatorException(f'Unexpected field type {schema["type"]}: {collection.name}.{field}')

            if not is_polymorphic_many_to_one(schema):
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

        type_ = TypeGetter.get(value, column_type)

        if value is None and {"operator": Operator.PRESENT} not in schema["validations"]:
            return

        if column_type == PrimitiveType.ENUM:
            cls.check_enum_value(type_, schema, value)

        if allowed_types:
            if type_ not in allowed_types:
                raise FieldValidatorException(f'Wrong type for "{field}": {value}. Expects [{allowed_types}]')
        elif type_ != column_type:
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

    @staticmethod
    def validate_name(collection_name: str, name: str):
        if " " in name:
            sanitized_name = re.sub(r" (.)", lambda m: m.group(1).upper(), name)
            raise FieldValidatorException(
                f"The name of field '{name}' you configured on '{collection_name}' must not contain space. "
                f"Something like '{sanitized_name}' should work has expected."
            )
