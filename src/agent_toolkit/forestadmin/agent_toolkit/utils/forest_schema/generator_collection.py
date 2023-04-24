from typing import List, Union

from forestadmin.agent_toolkit.utils.forest_schema.generator_action import SchemaActionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.agent_toolkit.utils.forest_schema.generator_segment import SchemaSegmentGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerCollection, ForestServerField
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
from forestadmin.datasource_toolkit.interfaces.fields import FieldType
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaCollectionGenerator:
    @staticmethod
    async def build(prefix: str, collection: Union[Collection, CustomizedCollection]) -> ForestServerCollection:
        fields: List[ForestServerField] = []
        for field_name in collection.schema["fields"].keys():
            if not SchemaUtils.is_foreign_key(collection.schema, field_name):
                fields.append(SchemaFieldGenerator.build(collection, field_name))

        return {
            "name": collection.name,
            "isVirtual": False,  # TODO: compute it
            "icon": None,
            "isReadOnly": all(
                [f["type"] == FieldType.COLUMN and f["is_read_only"] for f in collection.schema["fields"].values()]
            ),
            "integration": None,  # TODO: ???
            "isSearchable": collection.schema["searchable"],
            "onlyForRelationships": False,
            "paginationType": "page",
            "searchField": None,
            "actions": [
                await SchemaActionGenerator.build(prefix, collection, name)
                for name in collection.schema["actions"].keys()
            ],
            "segments": [
                await SchemaSegmentGenerator.build(collection, name) for name in collection.schema["segments"]
            ],
            "fields": fields,
        }
