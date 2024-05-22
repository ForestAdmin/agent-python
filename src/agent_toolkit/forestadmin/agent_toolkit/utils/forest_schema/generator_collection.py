from typing import List

from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.agent_toolkit.utils.forest_schema.generator_segment import SchemaSegmentGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerCollection, ForestServerField
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaCollectionGenerator:
    @staticmethod
    async def build(prefix: str, collection: Collection) -> ForestServerCollection:
        fields: List[ForestServerField] = []
        for field_name in collection.schema["fields"].keys():
            if SchemaUtils.is_foreign_key(collection.schema, field_name) and not SchemaUtils.is_primary_key(
                collection.schema, field_name
            ):
                # ignore foreign key because we have relationships, except when the fk is pk
                continue
            fields.append(SchemaFieldGenerator.build(collection, field_name))
        fields = sorted(fields, key=lambda field: field["field"])

        ret: ForestServerCollection = {
            "name": collection.name,
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
            "fields": fields,
        }

        # removing default values
        for field, default_value in {
            "action": [],
            "segments": [],
        }.items():
            if ret.get(field) == default_value:
                ret.pop(field, None)  # type:ignore
        return ret
