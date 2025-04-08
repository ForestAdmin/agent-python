import json
from enum import Enum
from typing import Any, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
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
from forestadmin.rpc_common.serializers.actions import ActionSerializer
from forestadmin.rpc_common.serializers.utils import OperatorSerializer, enum_to_str_or_value


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

    async def serialize(self) -> dict:
        value = (
            {
                "charts": sorted(self.datasource.schema["charts"].keys()),
                "live_query_connections": sorted(self.datasource.get_native_query_connections()),
                "collections": [
                    await self._serialize_collection(c)
                    for c in sorted(self.datasource.collections, key=lambda c: c.name)
                ],
            },
        )
        return value

    async def _serialize_collection(self, collection: Collection) -> dict:
        return {
            "name": collection.name,
            "fields": {
                field: await self._serialize_field(collection.schema["fields"][field])
                for field in sorted(collection.schema["fields"].keys())
            },
            "actions": {
                action_name: await ActionSerializer.serialize(action_name, collection)
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
            "column_type": (serialize_column_type(column["column_type"])),
            "filter_operators": sorted([OperatorSerializer.serialize(op) for op in column.get("filter_operators", [])]),
            "default_value": column.get("default_value"),
            "enum_values": column.get("enum_values"),
            "is_primary_key": column.get("is_primary_key", False),
            "is_read_only": column.get("is_read_only", False),
            "is_sortable": column.get("is_sortable", False),
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
                    "foreign_collections": relation["foreign_collections"],
                    "foreign_key": relation["foreign_key"],
                    "foreign_key_type_field": relation["foreign_key_type_field"],
                    "foreign_key_targets": relation["foreign_key_targets"],
                }
            )
        elif is_many_to_one(relation):
            serialized_field.update(
                {
                    "type": "ManyToOne",
                    "foreign_collection": relation["foreign_collection"],
                    "foreign_key": relation["foreign_key"],
                    "foreign_key_target": relation["foreign_key_target"],
                }
            )
        elif is_one_to_one(relation) or is_one_to_many(relation):
            serialized_field.update(
                {
                    "type": "OneToMany" if is_one_to_many(relation) else "OneToOne",
                    "foreign_collection": relation["foreign_collection"],
                    "origin_key": relation["origin_key"],
                    "origin_key_target": relation["origin_key_target"],
                }
            )
        elif is_polymorphic_one_to_one(relation) or is_polymorphic_one_to_many(relation):
            serialized_field.update(
                {
                    "type": "PolymorphicOneToMany" if is_polymorphic_one_to_many(relation) else "PolymorphicOneToOne",
                    "foreign_collection": relation["foreign_collection"],
                    "origin_key": relation["origin_key"],
                    "origin_key_target": relation["origin_key_target"],
                    "origin_type_field": relation["origin_type_field"],
                    "origin_type_value": relation["origin_type_value"],
                }
            )
        elif is_many_to_many(relation):
            serialized_field.update(
                {
                    "type": "ManyToMany",
                    "foreign_collections": relation["foreign_collection"],
                    "foreign_key": relation["foreign_key"],
                    "foreign_key_targets": relation["foreign_key_target"],
                    "origin_key": relation["origin_key"],
                    "origin_key_target": relation["origin_key_target"],
                    "through_collection": relation["through_collection"],
                }
            )
        return serialized_field


class SchemaDeserializer:
    VERSION = "1.0"

    def deserialize(self, schema) -> dict:
        return {
            "charts": schema["charts"],
            # "live_query_connections": schema["data"]["live_query_connections"],
            "collections": {
                collection["name"]: self._deserialize_collection(collection) for collection in schema["collections"]
            },
        }

    def _deserialize_collection(self, collection: dict) -> dict:
        return {
            "fields": {field: self._deserialize_field(collection["fields"][field]) for field in collection["fields"]},
            "actions": {
                action_name: ActionSerializer.deserialize(action)
                for action_name, action in collection["actions"].items()
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
            "column_type": deserialize_column_type(column["column_type"]),
            "filter_operators": [OperatorSerializer.deserialize(op) for op in column["filter_operators"]],
            "default_value": column.get("default_value"),
            "enum_values": column.get("enum_values"),
            "is_primary_key": column.get("is_primary_key", False),
            "is_read_only": column.get("is_read_only", False),
            "is_sortable": column.get("is_sortable", False),
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
                "foreign_collections": relation["foreign_collections"],
                "foreign_key": relation["foreign_key"],
                "foreign_key_type_field": relation["foreign_key_type_field"],
                "foreign_key_targets": relation["foreign_key_targets"],
            }
        elif relation["type"] == "ManyToOne":
            return {
                "type": FieldType("ManyToOne"),
                "foreign_collection": relation["foreign_collection"],
                "foreign_key": relation["foreign_key"],
                "foreign_key_target": relation["foreign_key_target"],
            }
        elif relation["type"] in ["OneToMany", "OneToOne"]:
            return {
                "type": FieldType("OneToOne") if relation["type"] == "OneToOne" else FieldType("OneToMany"),
                "foreign_collection": relation["foreign_collection"],
                "origin_key": relation["origin_key"],
                "origin_key_target": relation["origin_key_target"],
            }
        elif relation["type"] in ["PolymorphicOneToMany", "PolymorphicOneToOne"]:
            return {
                "type": (
                    FieldType("PolymorphicOneToOne")
                    if relation["type"] == "PolymorphicOneToOne"
                    else FieldType("PolymorphicOneToMany")
                ),
                "foreign_collection": relation["foreign_collection"],
                "origin_key": relation["origin_key"],
                "origin_key_target": relation["origin_key_target"],
                "origin_type_field": relation["origin_type_field"],
                "origin_type_value": relation["origin_type_value"],
            }
        elif relation["type"] == "ManyToMany":
            return {
                "type": FieldType("ManyToMany"),
                "foreign_collection": relation["foreign_collections"],
                "foreign_key": relation["foreign_key"],
                "foreign_key_target": relation["foreign_key_targets"],
                "origin_key": relation["origin_key"],
                "origin_key_target": relation["origin_key_target"],
                "through_collection": relation["through_collection"],
            }
        raise ValueError(f"Unsupported relation type {relation['type']}")
