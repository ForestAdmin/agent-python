from typing import List

from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.generator_field_v2 import SchemaFieldGeneratorV2
from forestadmin.agent_toolkit.utils.forest_schema.generator_segment import SchemaSegmentGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type_v2 import SchemaV2Collection, SchemaV2Field, SchemaV2Relation
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import is_column


class SchemaCollectionGeneratorV2:
    @staticmethod
    async def build(prefix: str, collection: Collection) -> SchemaV2Collection:
        fields: List[SchemaV2Field] = []
        relations: List[SchemaV2Relation] = []
        for field_name in collection.schema["fields"].keys():
            field_schema = collection.get_field(field_name)
            if is_column(field_schema):
                fields.append(SchemaFieldGeneratorV2.build_field(collection, field_name))
            else:
                relations.append(SchemaFieldGeneratorV2.build_relation(collection, field_name))

        return {
            "name": collection.name,
            "fields": sorted(fields, key=lambda field: field["name"]),
            "relations": sorted(relations, key=lambda field: field["name"]),
            "actions": sorted(
                [
                    await SchemaActionGenerator.build(prefix, collection, name)
                    for name in collection.schema["actions"].keys()
                ],
                key=lambda action: action["id"],
            ),
            "segments": sorted(
                [await SchemaSegmentGenerator.build(collection, name) for name in collection.schema["segments"]],
                key=lambda segment: segment["id"],
            ),
            # capabilities
            "canSearch": collection.schema["searchable"],
            "canList": collection.schema["listable"],
            "canCreate": collection.schema["creatable"],
            "canUpdate": collection.schema["updatable"],
            "canDelete": collection.schema["deletable"],
            "canCount": collection.schema["countable"],
            "canChart": collection.schema["chartable"],
            "canNativeQuery": collection.schema["support_native_query"],
        }
