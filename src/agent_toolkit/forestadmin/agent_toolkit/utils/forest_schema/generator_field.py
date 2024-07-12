from typing import Dict, Union, cast

from forestadmin.agent_toolkit.utils.forest_schema.filterable import FrontendFilterableUtils
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerField, RelationServer
from forestadmin.agent_toolkit.utils.forest_schema.validation import FrontendValidationUtils
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ColumnAlias,
    FieldType,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    Operator,
    PrimitiveType,
    RelationAlias,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaFieldGenerator:
    RELATION_MAPPING: Dict[FieldType, RelationServer] = {
        FieldType.ONE_TO_ONE: "HasOne",
        FieldType.ONE_TO_MANY: "HasMany",
        FieldType.MANY_TO_ONE: "BelongsTo",
        FieldType.MANY_TO_MANY: "BelongsToMany",
    }

    @classmethod
    def build(cls, collection: Union[Collection, CollectionCustomizer], field_name: str) -> ForestServerField:
        schema: ForestServerField = {}

        field_schema = collection.get_field(field_name)
        if is_column(field_schema):
            schema = cls.build_column_schema(field_name, collection)
        elif (
            is_one_to_one(field_schema)
            or is_one_to_many(field_schema)
            or is_many_to_one(field_schema)
            or is_many_to_many(field_schema)
        ):
            schema = cls.build_relation_schema(collection, field_name, field_schema)
        else:
            raise
        return cast(ForestServerField, dict(sorted(schema.items())))

    @staticmethod
    def build_column_type(_column_type: ColumnAlias) -> ColumnAlias:
        column_type: ColumnAlias
        if isinstance(_column_type, PrimitiveType):
            column_type = _column_type.value
        elif isinstance(_column_type, str):
            column_type = _column_type
        elif isinstance(_column_type, list):
            column_type = [SchemaFieldGenerator.build_column_type(_column_type[0])]
        else:
            column_type = {
                "fields": [
                    {"field": k, "type": SchemaFieldGenerator.build_column_type(t)} for k, t in _column_type.items()
                ]
            }
        return column_type

    @classmethod
    def build_column_schema(cls, name: str, collection: Collection) -> ForestServerField:
        column: Column = collection.schema["fields"][name]  #  type:ignore
        validations = []
        if column["validations"]:
            validations = column["validations"]

        is_foreign_key = SchemaUtils.is_foreign_key(collection.schema, name)

        res = {
            "field": name,
            "type": cls.build_column_type(column["column_type"]),
            "validations": FrontendValidationUtils.convert_validation_list(column["validations"]),
            "defaultValue": column["default_value"],
            "enums": sorted(column["enum_values"]) if column.get("enum_values") is not None else None,
            "inverseOf": None,
            "isFilterable": FrontendFilterableUtils.is_filterable(column["column_type"], column["filter_operators"]),
            "isPrimaryKey": bool(column["is_primary_key"]),
            "isSortable": bool(column["is_sortable"]),
            # When a column is a foreign key, it is readonly.
            # This may sound counter-intuitive: it is so that the user don't have two fields which
            # allow updating the same foreign key in the detail-view form (fk + many to one)
            "isReadOnly": is_foreign_key or bool(column["is_read_only"]),
            "isRequired": any([v["operator"] == Operator.PRESENT for v in validations]),
            "reference": None,
        }
        return ForestServerField(**res)

    @staticmethod
    def is_foreign_collection_filterable(foreign_collection: Collection) -> bool:
        res = False
        for field in foreign_collection.schema["fields"].values():
            if is_column(field) and FrontendFilterableUtils.is_filterable(
                field["column_type"], field["filter_operators"]
            ):
                res = True
                break
        return res

    @classmethod
    def build_one_to_one_schema(
        cls, relation: OneToOne, collection: Collection, foreign_collection: Collection, base_schema: ForestServerField
    ) -> ForestServerField:
        target_field = collection.schema["fields"][relation["origin_key_target"]]
        key_field = foreign_collection.schema["fields"][relation["origin_key"]]

        return {
            **base_schema,
            "type": cls.build_column_type(key_field["column_type"]),
            "defaultValue": None,
            "isFilterable": cls.is_foreign_collection_filterable(foreign_collection),
            "isPrimaryKey": False,
            "isRequired": False,
            "isReadOnly": bool(key_field["is_read_only"]),
            "isSortable": bool(target_field["is_sortable"]),
            "validations": [],
            "reference": f"{foreign_collection.name}.{relation['origin_key']}",
        }

    @classmethod
    def build_to_many_relation_schema(
        cls,
        relation: Union[OneToMany, ManyToMany],
        collection: Collection,
        foreign_collection: Collection,
        base_schema: ForestServerField,
    ) -> ForestServerField:
        if is_one_to_many(relation):
            key = relation["origin_key_target"]
            key_schema = cast(Column, collection.get_field(key))
        else:
            key = relation["foreign_key_target"]
            key_schema = cast(Column, foreign_collection.get_field(key))

        return {
            **base_schema,
            "type": [cls.build_column_type(key_schema["column_type"])],
            "defaultValue": None,
            "isFilterable": False,
            "isPrimaryKey": False,
            "isRequired": False,
            "isSortable": True,
            "validations": [],
            "reference": f"{foreign_collection.name}.{key}",
        }

    @classmethod
    def build_many_to_one_schema(
        cls,
        relation: ManyToOne,
        collection: Union[CollectionCustomizer, Collection],
        foreign_collection: Collection,
        base_schema: ForestServerField,
    ) -> ForestServerField:
        key = relation["foreign_key"]
        key_schema = cast(Column, collection.get_field(key))
        validations = key_schema["validations"] or []

        return {
            **base_schema,
            "type": cls.build_column_type(key_schema["column_type"]),
            "defaultValue": key_schema["default_value"],
            "isFilterable": cls.is_foreign_collection_filterable(foreign_collection),
            "isPrimaryKey": False,
            "isRequired": any([v["operator"] == Operator.PRESENT for v in validations]),
            "isSortable": bool(key_schema["is_sortable"]),
            "validations": FrontendValidationUtils.convert_validation_list(validations),
            "reference": f"{foreign_collection.name}.{relation['foreign_key_target']}",
        }

    @classmethod
    def build_relation_schema(
        cls, collection: Union[Collection, CollectionCustomizer], field_name: str, field_schema: RelationAlias
    ) -> ForestServerField:
        foreign_collection = collection.datasource.get_collection(field_schema["foreign_collection"])
        relation_schema: ForestServerField = {
            "field": field_name,
            "enums": None,
            "isReadOnly": False,
            "inverseOf": CollectionUtils.get_inverse_relation(cast(Collection, collection), field_name),
            "relationship": cls.RELATION_MAPPING[field_schema["type"]],
        }
        if is_many_to_many(field_schema) or is_one_to_many(field_schema):
            res = cls.build_to_many_relation_schema(field_schema, collection, foreign_collection, relation_schema)
        elif is_one_to_one(field_schema):
            res = cls.build_one_to_one_schema(field_schema, collection, foreign_collection, relation_schema)
        else:
            res = cls.build_many_to_one_schema(
                cast(ManyToOne, field_schema), collection, foreign_collection, relation_schema
            )
        return res
