from typing import Any, Dict, List, Literal, Union

from forestadmin.agent_toolkit.options import AgentMeta, Options
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection import SchemaCollectionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerCollection
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource import CustomizedDatasource


class SchemaEmitter:
    @staticmethod
    def get_serialized_collection_relation(
        collection: ForestServerCollection, rel_type: Literal["actions", "segments"]
    ):
        data: List[Dict[str, str]] = []
        included: List[Dict[str, str]] = []
        for rel in collection.get(rel_type, []):  # type: ignore
            try:
                name: str = rel["name"]
            except TypeError:
                name: str = rel
            id = f"{collection['name']}.{name}"
            data.append({"id": id, "type": rel_type})
            included.append({"id": id, "type": rel_type, "attributes": rel})

        return data, included

    @classmethod
    def serialize(cls, collections: List[ForestServerCollection], meta: AgentMeta) -> Dict[str, Any]:
        serialized_collections: List[Dict[str, Any]] = []
        included: List[Dict[str, str]] = []
        for collection in collections:
            action_data, action_included = cls.get_serialized_collection_relation(collection, "actions")
            segment_data, segment_included = cls.get_serialized_collection_relation(collection, "segments")
            included.extend(action_included)
            included.extend(segment_included)
            serialized_collections.append(
                {
                    "id": collection["name"],
                    "type": "collections",
                    "attributes": collection,
                    "relationships": {"actions": {"data": action_data}, "segments": {"data": segment_data}},
                }
            )
        return {"data": serialized_collections, "included": included, "meta": meta}

    @classmethod
    async def get_serialized_schema(
        cls, options: Options, datasource: Union[Datasource[Collection], CustomizedDatasource], meta: AgentMeta
    ):
        schema: List[ForestServerCollection] = []
        if not options["is_production"]:
            schema = await SchemaEmitter.generate(options["prefix"], datasource)
        return schema

    @staticmethod
    async def generate(
        prefix: str, datasource: Union[Datasource[Collection], CustomizedDatasource]
    ) -> List[ForestServerCollection]:
        collection_schema: List[ForestServerCollection] = []
        for collection in datasource.collections:
            collection_schema.append(await SchemaCollectionGenerator.build(prefix, collection))
        return collection_schema
