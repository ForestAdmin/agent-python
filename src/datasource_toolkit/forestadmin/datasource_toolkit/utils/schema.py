from typing import List

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import is_column, is_many_to_many
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class SchemaUtilsException(DatasourceToolkitException):
    pass


class SchemaUtils:
    @staticmethod
    def get_primary_keys(schema: CollectionSchema) -> List[str]:
        pks: List[str] = []
        for name, field in schema["fields"].items():
            if is_column(field) and field.get("is_primary_key", False):
                pks.append(name)
        return pks

    @staticmethod
    def is_foreign_key(schema: CollectionSchema, name: str) -> bool:
        field = schema["fields"][name]
        for relation in schema["fields"].values():
            if is_many_to_many(relation) and relation["foreign_key"] == name:
                break
        else:
            return False
        return is_column(field)
