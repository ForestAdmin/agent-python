from typing import List, Union

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    ManyToMany,
    OneToMany,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
)
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
            if (is_many_to_one(relation)) and relation["foreign_key"] == name:
                break
        else:
            return False
        return is_column(field)

    @staticmethod
    def is_primary_key(schema: CollectionSchema, name: str) -> bool:
        field = schema["fields"][name]

        return is_column(field) and field.get("is_primary_key", False)

    @staticmethod
    def get_to_many_relation(schema: CollectionSchema, relation_name: str) -> Union[ManyToMany, OneToMany]:
        try:
            relation_field = schema["fields"][relation_name]
        except KeyError:
            raise SchemaUtilsException(f"Relation {relation_name} not found")

        if not is_many_to_many(relation_field) and not is_one_to_many(relation_field):
            raise SchemaUtilsException(
                f"Relation {relation_name} has invalid type should be one of OneToMany or ManyToMany"
            )
        return relation_field
