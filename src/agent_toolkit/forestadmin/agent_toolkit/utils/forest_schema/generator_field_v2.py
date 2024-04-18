from typing import cast

from forestadmin.agent_toolkit.utils.forest_schema.type_v2 import SchemaV2Field, SchemaV2Relation
from forestadmin.agent_toolkit.utils.forest_schema.validation import FrontendValidationUtils
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ColumnAlias,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PrimitiveType,
    RelationAlias,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)


class SchemaFieldGeneratorV2:
    @classmethod
    def _convert_operator(cls, operator: Operator) -> str:
        return operator.value.replace("_", " ").title().replace(" ", "")

    @classmethod
    def build_field(cls, collection: Collection, field_name: str) -> SchemaV2Field:
        field_schema: Column = cast(Column, collection.get_field(field_name))
        return {
            "name": field_name,
            "type": cls.build_column_type(field_schema["column_type"]),
            "filterOperators": sorted(
                [
                    SchemaFieldGeneratorV2._convert_operator(operator)
                    for operator in field_schema["filter_operators"] or {}
                ]
            ),
            "enumerations": (
                field_schema["enum_values"] if field_schema["enum_values"] is not None else []
            ),  # type:ignore
            "isPrimaryKey": field_schema["is_primary_key"],
            "isSortable": field_schema["is_sortable"],
            "isWritable": not field_schema["is_read_only"],
            "prefillFormValue": field_schema["default_value"],
            "validations": FrontendValidationUtils.convert_validation_list(field_schema["validations"]),
        }

    @staticmethod
    def build_column_type(_column_type: ColumnAlias) -> ColumnAlias:
        column_type: ColumnAlias
        if isinstance(_column_type, PrimitiveType):
            column_type = _column_type.value
        elif isinstance(_column_type, str):
            column_type = _column_type
        elif isinstance(_column_type, list):
            column_type = [SchemaFieldGeneratorV2.build_column_type(_column_type[0])]
        else:
            column_type = {
                "fields": [
                    {"field": k, "type": SchemaFieldGeneratorV2.build_column_type(t)} for k, t in _column_type.items()
                ]
            }  # type:ignore

        return column_type

    @classmethod
    def build_relation(cls, collection: Collection, relation_name: str) -> SchemaV2Relation:
        field_schema: RelationAlias = cast(RelationAlias, collection.get_field(relation_name))
        if is_many_to_many(field_schema):
            return SchemaFieldGeneratorV2.build_many_to_many_schema(field_schema, relation_name)
        elif is_many_to_one(field_schema):
            return SchemaFieldGeneratorV2.build_many_to_one_schema(field_schema, relation_name)
        elif is_one_to_many(field_schema):
            return SchemaFieldGeneratorV2.build_one_to_many_schema(field_schema, relation_name)
        elif is_one_to_one(field_schema):
            return SchemaFieldGeneratorV2.build_one_to_one_schema(field_schema, relation_name)
        else:
            raise

    @classmethod
    def build_one_to_one_schema(cls, relation: OneToOne, relation_name: str) -> SchemaV2Relation:
        return {
            "name": relation_name,
            "type": "OneToOne",
            "foreignCollection": relation["foreign_collection"],
            "originKey": relation["origin_key"],
            "originKeyTarget": relation["origin_key_target"],
        }

    @classmethod
    def build_many_to_one_schema(cls, relation: ManyToOne, relation_name: str) -> SchemaV2Relation:
        return {
            "name": relation_name,
            "type": "ManyToOne",
            "foreignCollection": relation["foreign_collection"],
            "foreignKey": relation["foreign_key"],
            "foreignKeyTarget": relation["foreign_key_target"],
        }

    @classmethod
    def build_one_to_many_schema(cls, relation: OneToMany, relation_name: str) -> SchemaV2Relation:
        return {
            "name": relation_name,
            "type": "OneToMany",
            "foreignCollection": relation["foreign_collection"],
            "originKey": relation["origin_key"],
            "originKeyTarget": relation["origin_key_target"],
        }

    @classmethod
    def build_many_to_many_schema(cls, relation: ManyToMany, relation_name: str) -> SchemaV2Relation:
        return {
            "name": relation_name,
            "type": "ManyToMany",
            "foreignCollection": relation["foreign_collection"],
            "throughCollection": relation["through_collection"],
            "originKey": relation["origin_key"],
            "originKeyTarget": relation["origin_key_target"],
            "foreignKey": relation["foreign_key"],
            "foreignKeyTarget": relation["foreign_key_target"],
        }
