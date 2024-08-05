from typing import Any

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class RecordUtilsException(DatasourceToolkitException):
    pass


class RecordUtils:
    @staticmethod
    def get_primary_key(schema: CollectionSchema, record: RecordsDataAlias) -> CompositeIdAlias:
        results: CompositeIdAlias = []
        for pk in SchemaUtils.get_primary_keys(schema):
            try:
                field = record[pk]
            except KeyError:
                raise RecordUtilsException(f"Missing primary key: {pk}")
            else:
                results.append(field)
        return results

    @staticmethod
    def get_field_value(record: RecordsDataAlias, field: str) -> Any:
        current_record = record
        for path in field.split(":"):
            if current_record:
                current_record = current_record.get(path)
        return current_record
