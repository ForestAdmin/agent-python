import json
from enum import Enum
from typing import Any, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType, ActionsScope
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    FieldAlias,
    FieldType,
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
from forestadmin.rpc_common.serializers.utils import OperatorSerializer, enum_to_str_or_value, snake_to_camel_case


def serialize_column_type(column_type: Union[Enum, Any]) -> Union[str, dict, list]:
    if isinstance(column_type, list):
        return [serialize_column_type(t) for t in column_type]

    if isinstance(column_type, dict):
        return {k: serialize_column_type(v) for k, v in column_type.items()}

    return enum_to_str_or_value(column_type)


def deserialize_column_type(column_type: Union[list, dict, str]) -> Union[PrimitiveType, dict, list]:
    if isinstance(column_type, list):
        return [deserialize_column_type(t) for t in column_type]

    if isinstance(column_type, dict):
        return {k: deserialize_column_type(v) for k, v in column_type.items()}

    return PrimitiveType(column_type)


class SchemaSerializer:
    VERSION = "1.0"

    def __init__(self, datasource: Datasource) -> None:
        self.datasource = datasource

    async def serialize(self) -> str:
        value = {
            "version": self.VERSION,
            "data": {
                "charts": sorted(self.datasource.schema["charts"].keys()),
                "live_query_connections": sorted(self.datasource.get_native_query_connections()),
                "collections": {
                    c.name: await self._serialize_collection(c)
                    for c in sorted(self.datasource.collections, key=lambda c: c.name)
                },
            },
        }
        return json.dumps(value)

    async def _serialize_collection(self, collection: Collection) -> dict:
        return {
            "fields": {
                field: await self._serialize_field(collection.schema["fields"][field])
                for field in sorted(collection.schema["fields"].keys())
            },
            "actions": {
                action_name: await self._serialize_action(action_name, collection)
                for action_name in sorted(collection.schema["actions"].keys())
            },
            "segments": sorted(collection.schema["segments"]),
            "countable": collection.schema["countable"],
            "searchable": collection.schema["searchable"],
            "charts": sorted(collection.schema["charts"].keys()),
        }

    async def _serialize_field(self, field: FieldAlias) -> dict:
        if is_column(field):
            return await self._serialize_column(field)
        else:
            return await self._serialize_relation(cast(RelationAlias, field))

    async def _serialize_column(self, column: Column) -> dict:
        return {
            "type": "Column",
            "columnType": (serialize_column_type(column["column_type"])),
            "filterOperators": sorted([OperatorSerializer.serialize(op) for op in column.get("filter_operators", [])]),
            "defaultValue": column.get("default_value"),
            "enumValues": column.get("enum_values"),
            "isPrimaryKey": column.get("is_primary_key", False),
            "isReadOnly": column.get("is_read_only", False),
            "isSortable": column.get("is_sortable", False),
            "validations": [
                {
                    "operator": OperatorSerializer.serialize(v["operator"]),
                    "value": v.get("value"),
                }
                for v in sorted(
                    column.get("validations", []),
                    key=lambda v: f'{OperatorSerializer.serialize(v["operator"])}_{str(v.get("value"))}',
                )
            ],
        }

    async def _serialize_relation(self, relation: RelationAlias) -> dict:
        serialized_field = {}
        if is_polymorphic_many_to_one(relation):
            serialized_field.update(
                {
                    "type": "PolymorphicManyToOne",
                    "foreignCollections": relation["foreign_collections"],
                    "foreignKey": relation["foreign_key"],
                    "foreignKeyTypeField": relation["foreign_key_type_field"],
                    "foreignKeyTargets": relation["foreign_key_targets"],
                }
            )
        elif is_many_to_one(relation):
            serialized_field.update(
                {
                    "type": "ManyToOne",
                    "foreignCollection": relation["foreign_collection"],
                    "foreignKey": relation["foreign_key"],
                    "foreignKeyTarget": relation["foreign_key_target"],
                }
            )
        elif is_one_to_one(relation) or is_one_to_many(relation):
            serialized_field.update(
                {
                    "type": "OneToMany" if is_one_to_many(relation) else "OneToOne",
                    "foreignCollection": relation["foreign_collection"],
                    "originKey": relation["origin_key"],
                    "originKeyTarget": relation["origin_key_target"],
                }
            )
        elif is_polymorphic_one_to_one(relation) or is_polymorphic_one_to_many(relation):
            serialized_field.update(
                {
                    "type": "PolymorphicOneToMany" if is_polymorphic_one_to_many(relation) else "PolymorphicOneToOne",
                    "foreignCollection": relation["foreign_collection"],
                    "originKey": relation["origin_key"],
                    "originKeyTarget": relation["origin_key_target"],
                    "originTypeField": relation["origin_type_field"],
                    "originTypeValue": relation["origin_type_value"],
                }
            )
        elif is_many_to_many(relation):
            serialized_field.update(
                {
                    "type": "ManyToMany",
                    "foreignCollections": relation["foreign_collection"],
                    "foreignKey": relation["foreign_key"],
                    "foreignKeyTargets": relation["foreign_key_target"],
                    "originKey": relation["origin_key"],
                    "originKeyTarget": relation["origin_key_target"],
                    "throughCollection": relation["through_collection"],
                }
            )
        return serialized_field

    async def _serialize_action(self, action_name: str, collection: Collection) -> dict:
        action = collection.schema["actions"][action_name]
        if not action.static_form:
            form = None
        else:
            form = await collection.get_form(None, action_name, None, None)  # type:ignore
            # fields, layout = SchemaActionGenerator.extract_fields_and_layout(form)
            # fields = [
            #     await SchemaActionGenerator.build_field_schema(collection.datasource, field) for field in fields
            # ]

        return {
            "scope": action.scope.value,
            "generateFile": action.generate_file or False,
            "staticForm": action.static_form or False,
            "description": action.description,
            "submitButtonLabel": action.submit_button_label,
            "form": await self._serialize_action_form(form) if form is not None else None,
        }

    async def _serialize_action_form(self, form) -> list[dict]:
        serialized_form = []

        for field in form:
            if field["type"] == ActionFieldType.LAYOUT:
                if field["component"] == "Page":
                    serialized_form.append(
                        {**field, "type": "Layout", "elements": await self._serialize_action_form(field["elements"])}
                    )

                if field["component"] == "Row":
                    serialized_form.append(
                        {**field, "type": "Layout", "fields": await self._serialize_action_form(field["fields"])}
                    )
            else:
                serialized_form.append(
                    {
                        **{snake_to_camel_case(k): v for k, v in field.items()},
                        "type": enum_to_str_or_value(field["type"]),
                    }
                )

        return serialized_form


class SchemaDeserializer:
    VERSION = "1.0"

    def deserialize(self, json_schema) -> dict:
        schema = json.loads(json_schema)
        if schema["version"] != self.VERSION:
            raise ValueError(f"Unsupported schema version {schema['version']}")

        return {
            "charts": schema["data"]["charts"],
            "live_query_connections": schema["data"]["live_query_connections"],
            "collections": {
                name: self._deserialize_collection(collection)
                for name, collection in schema["data"]["collections"].items()
            },
        }

    def _deserialize_collection(self, collection: dict) -> dict:
        return {
            "fields": {field: self._deserialize_field(collection["fields"][field]) for field in collection["fields"]},
            "actions": {
                action_name: self._deserialize_action(action) for action_name, action in collection["actions"].items()
            },
            "segments": collection["segments"],
            "countable": collection["countable"],
            "searchable": collection["searchable"],
            "charts": collection["charts"],
        }

    def _deserialize_field(self, field: dict) -> dict:
        if field["type"] == "Column":
            return self._deserialize_column(field)
        else:
            return self._deserialize_relation(field)

    def _deserialize_column(self, column: dict) -> dict:
        return {
            "type": FieldType.COLUMN,
            "column_type": deserialize_column_type(column["columnType"]),
            "filter_operators": [OperatorSerializer.deserialize(op) for op in column["filterOperators"]],
            "default_value": column.get("defaultValue"),
            "enum_values": column.get("enumValues"),
            "is_primary_key": column.get("isPrimaryKey", False),
            "is_read_only": column.get("isReadOnly", False),
            "is_sortable": column.get("isSortable", False),
            "validations": [
                {
                    "operator": OperatorSerializer.deserialize(op["operator"]),
                    "value": op.get("value"),
                }
                for op in column.get("validations", [])
            ],
        }

    def _deserialize_relation(self, relation: dict) -> dict:
        if relation["type"] == "PolymorphicManyToOne":
            return {
                "type": FieldType("PolymorphicManyToOne"),
                "foreign_collections": relation["foreignCollections"],
                "foreign_key": relation["foreignKey"],
                "foreign_key_type_field": relation["foreignKeyTypeField"],
                "foreign_key_targets": relation["foreignKeyTargets"],
            }
        elif relation["type"] == "ManyToOne":
            return {
                "type": FieldType("ManyToOne"),
                "foreign_collection": relation["foreignCollection"],
                "foreign_key": relation["foreignKey"],
                "foreign_key_target": relation["foreignKeyTarget"],
            }
        elif relation["type"] in ["OneToMany", "OneToOne"]:
            return {
                "type": FieldType("OneToOne") if relation["type"] == "OneToOne" else FieldType("OneToMany"),
                "foreign_collection": relation["foreignCollection"],
                "origin_key": relation["originKey"],
                "origin_key_target": relation["originKeyTarget"],
            }
        elif relation["type"] in ["PolymorphicOneToMany", "PolymorphicOneToOne"]:
            return {
                "type": (
                    FieldType("PolymorphicOneToOne")
                    if relation["type"] == "PolymorphicOneToOne"
                    else FieldType("PolymorphicOneToMany")
                ),
                "foreign_collection": relation["foreignCollection"],
                "origin_key": relation["originKey"],
                "origin_key_target": relation["originKeyTarget"],
                "origin_type_field": relation["originTypeField"],
                "origin_type_value": relation["originTypeValue"],
            }
        elif relation["type"] == "ManyToMany":
            return {
                "type": FieldType("ManyToMany"),
                "foreign_collection": relation["foreignCollections"],
                "foreign_key": relation["foreignKey"],
                "foreign_key_target": relation["foreignKeyTargets"],
                "origin_key": relation["originKey"],
                "origin_key_target": relation["originKeyTarget"],
                "through_collection": relation["throughCollection"],
            }
        raise ValueError(f"Unsupported relation type {relation['type']}")

    def _deserialize_action(self, action: dict) -> dict:
        return {
            "scope": ActionsScope(action["scope"]),
            "generate_file": action["generateFile"],
            "static_form": action["staticForm"],
            "description": action["description"],
            "submit_button_label": action["submitButtonLabel"],
            "form": self._deserialize_action_form(action["form"]) if action["form"] is not None else None,
        }

    def _deserialize_action_form(self, form: list) -> list[dict]:
        deserialized_form = []

        for field in form:
            if field["type"] == "Layout":
                if field["component"] == "Page":
                    deserialized_form.append(
                        {
                            **field,
                            "type": ActionFieldType("Layout"),
                            "elements": self._deserialize_action_form(field["elements"]),
                        }
                    )

                if field["component"] == "Row":
                    deserialized_form.append(
                        {
                            **field,
                            "type": ActionFieldType("Layout"),
                            "fields": self._deserialize_action_form(field["fields"]),
                        }
                    )
            else:
                deserialized_form.append(
                    {
                        **{snake_to_camel_case(k): v for k, v in field.items()},
                        "type": ActionFieldType(field["type"]),
                    }
                )

        return deserialized_form
