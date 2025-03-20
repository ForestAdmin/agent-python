from datetime import date, datetime
from typing import Any, Dict, cast
from uuid import UUID

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    PrimitiveType,
    RelationAlias,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class RecordSerializer:
    @staticmethod
    def serialize(record: RecordsDataAlias) -> Dict:
        serialized_record = {}

        for key, value in record.items():
            if isinstance(value, dict):
                serialized_record[key] = RecordSerializer.serialize(value)
            elif isinstance(value, set) or isinstance(value, list):
                serialized_record[key] = [RecordSerializer.serialize(v) for v in value]
            elif isinstance(value, date):
                serialized_record[key] = value.isoformat()
            # elif isinstance(value, datetime):
            #     serialized_record[key] = value.isoformat()
            elif isinstance(value, UUID):
                serialized_record[key] = str(value)
            else:
                serialized_record[key] = value

        return serialized_record

    @staticmethod
    def deserialize(record: Dict, collection: Collection) -> RecordsDataAlias:
        deserialized_record = {}
        collection_schema = collection.schema

        for key, value in record.items():
            if is_column(collection_schema["fields"][key]):
                deserialized_record[key] = RecordSerializer._deserialize_column(collection, key, value)
            else:
                deserialized_record[key] = RecordSerializer._deserialize_relation(collection, key, value, record)
        return deserialized_record

    @staticmethod
    def _deserialize_relation(collection: Collection, field_name: str, value: Any, record: Dict) -> RecordsDataAlias:
        schema_field = cast(RelationAlias, collection.schema["fields"][field_name])
        if is_many_to_one(schema_field) or is_one_to_one(schema_field) or is_polymorphic_one_to_one(schema_field):
            return RecordSerializer.deserialize(
                value, collection.datasource.get_collection(schema_field["foreign_collection"])
            )
        elif is_many_to_many(schema_field) or is_one_to_many(schema_field) or is_polymorphic_one_to_many(schema_field):
            return [
                RecordSerializer.deserialize(
                    v, collection.datasource.get_collection(schema_field["foreign_collection"])
                )
                for v in value
            ]
        elif is_polymorphic_many_to_one(schema_field):
            if schema_field["foreign_key_type_field"] not in record:
                raise ValueError("Cannot deserialize polymorphic many to one relation without foreign key type field")
            return RecordSerializer.deserialize(
                value, collection.datasource.get_collection(record[schema_field["foreign_key_type_field"]])
            )
        else:
            raise ValueError(f"Unknown field type: {schema_field}")

    @staticmethod
    def _deserialize_column(collection: Collection, field_name: str, value: Any) -> RecordsDataAlias:
        schema_field = cast(Column, collection.schema["fields"][field_name])

        if isinstance(schema_field["column_type"], dict) or isinstance(schema_field["column_type"], list):
            return RecordSerializer._deserialize_complex_type(schema_field["column_type"], value)
        elif isinstance(schema_field["column_type"], PrimitiveType):
            return RecordSerializer._deserialize_primitive_type(schema_field["column_type"], value)

    @staticmethod
    def _deserialize_primitive_type(type_: PrimitiveType, value: Any):
        if type_ == PrimitiveType.DATE:
            return datetime.fromisoformat(value)
        elif type_ == PrimitiveType.DATE_ONLY:
            return date.fromisoformat(value)
        elif type_ == PrimitiveType.DATE:
            return datetime.fromisoformat(value)
        elif type_ == PrimitiveType.POINT:
            return (value[0], value[1])
        elif type_ == PrimitiveType.UUID:
            return UUID(value)
        elif type_ == PrimitiveType.BINARY:
            pass  # TODO: binary
        elif type_ == PrimitiveType.TIME_ONLY:
            pass  # TODO: time only
        elif isinstance(type_, PrimitiveType):
            return value
        else:
            raise ValueError(f"Unknown primitive type: {type_}")

    @staticmethod
    def _deserialize_complex_type(type_, value):
        if isinstance(type_, list):
            return [RecordSerializer._deserialize_complex_type(type_[0], v) for v in value]
        elif isinstance(type_, dict):
            return {k: RecordSerializer._deserialize_complex_type(v, value[k]) for k, v in type_.items()}

        return value
