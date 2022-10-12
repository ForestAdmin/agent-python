from typing import Any, List, cast

from forestadmin.datasource_toolkit.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidator, FieldValidatorException


class IdException(BaseException):
    pass


def pack_id(schema: CollectionSchema, record: RecordsDataAlias):
    schema_pks = SchemaUtils.get_primary_keys(schema)
    if len(schema_pks) == 0:
        raise IdException("")
    pks = [str(record.get(pk, "")) for pk in schema_pks]
    if not all(pks):
        raise IdException("")

    return "|".join(pks)  # type: ignore


def unpack_id(schema: CollectionSchema, pks: str) -> CompositeIdAlias:

    schema_pks = SchemaUtils.get_primary_keys(schema)
    pk_values = pks.split("|")
    if len(pk_values) != len(schema_pks):
        raise IdException("Unable to unpack the id")

    values: List[Any] = []
    for i, field_name in enumerate(schema_pks):

        schema_field = cast(Column, schema["fields"][field_name])
        value = pk_values[i]

        if schema_field["column_type"] == PrimitiveType.NUMBER:
            try:
                value = int(value)
            except ValueError:
                value = float(value)
        try:
            FieldValidator.validate_value(field_name, schema_field, value)
        except FieldValidatorException:
            raise IdException("Unable to validate the id value")

        values.append(value)

    return values
