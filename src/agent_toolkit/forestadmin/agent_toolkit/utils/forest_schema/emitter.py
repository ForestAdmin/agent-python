import json
from hashlib import sha1
from typing import Any, Dict, List, Literal, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection import SchemaCollectionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta, ForestServerCollection
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource


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
            _id = f"{collection['name']}.{name}"
            data.append({"id": _id, "type": rel_type})
            included.append({"id": _id, "type": rel_type, "attributes": rel})

        return data, included

    @classmethod
    def serialize(cls, collections: List[ForestServerCollection], meta: AgentMeta) -> Dict[str, Any]:
        """return schema ready to send as api_map format"""
        serialized_collections: List[Dict[str, Any]] = []
        included: List[Dict[str, str]] = []
        schema_file_hash = sha1(json.dumps({"collections": collections, "meta": meta}).encode("utf-8")).hexdigest()
        for collection in collections:
            action_data, action_included = cls.get_serialized_collection_relation(collection, "actions")
            segment_data, segment_included = cls.get_serialized_collection_relation(collection, "segments")
            included.extend(action_included)
            included.extend(segment_included)
            collection_attributes = {
                key: value for key, value in collection.items() if key not in ["actions", "segments"]
            }
            serialized_collections.append(
                {
                    "id": collection["name"],
                    "type": "collections",
                    "attributes": collection_attributes,
                    "relationships": {"actions": {"data": action_data}, "segments": {"data": segment_data}},
                }
            )
        return {
            "data": serialized_collections,
            "included": included,
            "meta": {**meta, "schemaFileHash": schema_file_hash},
        }

    @classmethod
    async def get_serialized_schema(
        cls, options: Options, datasource: Union[Datasource[Collection], DatasourceCustomizer], meta: AgentMeta
    ):
        if not options["is_production"]:
            collections_schema = await SchemaEmitter.generate(options["prefix"], datasource)

            with open(options["schema_path"], "w", encoding="utf-8") as schema_file:
                json.dump({"collections": collections_schema, "meta": meta}, schema_file, indent=4)
        else:
            try:
                with open(options["schema_path"], "r", encoding="utf-8") as schema_file:
                    collections_schema = json.load(schema_file)["collections"]

            except Exception:
                ForestLogger.log(
                    "error",
                    f"Can't read {options['schema_path']}. Providing a schema is mandatory in production. Skipping...",
                )
                raise

        return cls.serialize(collections_schema, meta)

    @staticmethod
    async def generate(
        prefix: str, datasource: Union[Datasource[Collection], DatasourceCustomizer]
    ) -> List[ForestServerCollection]:
        """generate schema from datasource"""
        collection_schema: List[ForestServerCollection] = []
        for collection in datasource.collections:
            collection_schema.append(await SchemaCollectionGenerator.build(prefix, collection))
        return sorted(collection_schema, key=lambda collection: collection["name"])
