import json
from hashlib import sha1
from typing import Any, Dict, List, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection_v2 import SchemaCollectionGeneratorV2
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.agent_toolkit.utils.forest_schema.type_v2 import (
    SchemaV2Collection,
    template_apply_collection,
    template_apply_field,
)
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource


class SchemaEmitterV2:
    @classmethod
    def serialize(cls, collections: List[SchemaV2Collection], meta: AgentMeta) -> Dict[str, Any]:
        """return schema ready to send as api_map format"""
        schema_file_hash = sha1(json.dumps({"collections": collections, "meta": meta}).encode("utf-8")).hexdigest()
        return {
            "collections": collections,
            "meta": {
                **meta,
                "schemaFileHash": schema_file_hash,
            },
        }

    @classmethod
    async def get_serialized_schema(
        cls, options: Options, datasource: Union[Datasource[Collection], DatasourceCustomizer], meta: AgentMeta
    ):
        schema_path = f'{options["schema_path"].split(".json")[0]}_v2.json'
        full_schema_path = f'{options["schema_path"].split(".json")[0]}_full_v2.json'
        if not options["is_production"]:
            collections_schema = await SchemaEmitterV2.generate(options["prefix"], datasource)

            with open(schema_path, "w", encoding="utf-8") as schema_file:
                json.dump({"collections": collections_schema, "meta": meta}, schema_file, indent=4)

            with open(full_schema_path, "w", encoding="utf-8") as schema_file:
                full_collections = []
                for collection in collections_schema:
                    full_collections.append(
                        {
                            **template_apply_collection(collection),
                            "fields": [{**template_apply_field(f)} for f in collection["fields"]],
                        }
                    )
                json.dump({"collections": full_collections, "meta": meta}, schema_file, indent=4)
        else:
            try:
                with open(schema_path, "r", encoding="utf-8") as schema_file:
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
    ) -> List[SchemaV2Collection]:
        """generate schema from datasource"""
        collection_schema: List[SchemaV2Collection] = []
        for collection in datasource.collections:
            collection_schema.append(await SchemaCollectionGeneratorV2.build(prefix, collection))  # type:ignore
        return sorted(collection_schema, key=lambda collection: collection["name"])
