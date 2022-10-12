from typing import cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import is_column, is_many_to_one, is_one_to_one
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class RecordValidatorException(DatasourceToolkitException):
    pass


class RecordValidator:
    @classmethod
    def validate(cls, collection: Collection, record_data: RecordsDataAlias) -> None:
        if not record_data.keys():
            raise RecordValidatorException("The record data is empty")

        for field_name, record_value in record_data.items():
            try:
                schema = collection.schema["fields"][field_name]
            except KeyError:
                raise RecordValidatorException(f'Unknown field "{field_name}"')

            if is_column(schema):
                FieldValidator.validate(collection, field_name, [record_value])
            elif is_one_to_one(schema) or is_many_to_one(schema):
                nested_record = cast(RecordsDataAlias, record_value)
                association = collection.datasource.get_collection(schema["foreign_collection"])
                cls.validate(association, nested_record)
            else:
                raise RecordValidatorException(f'Unexpected schema type {schema["type"]} while traversing record')
