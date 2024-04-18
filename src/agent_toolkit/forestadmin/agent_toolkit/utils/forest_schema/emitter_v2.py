import json
from hashlib import sha1
from typing import Any, Dict, List, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection_v2 import SchemaCollectionGeneratorV2
from forestadmin.agent_toolkit.utils.forest_schema.type import AgentMeta
from forestadmin.agent_toolkit.utils.forest_schema.type_v2 import (
    AgentMetaV2,
    SchemaV2Collection,
    template_reduce_collection,
)
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator


class SchemaEmitterV2:
    @classmethod
    def serialize(
        cls,
        collections: List[SchemaV2Collection],
        meta: AgentMetaV2,
    ) -> Dict[str, Any]:
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
    def generate_meta(
        cls,
        meta: AgentMeta,
        datasource: Union[Datasource[Collection], DatasourceCustomizer],
    ) -> AgentMetaV2:
        used_datasources = set([_get_base_datasource(col) for col in datasource.collections])

        return {
            "agent": meta["liana"],
            "agent_version": meta["liana_version"],
            "stack": meta["stack"],
            "datasources": [d.mk_meta_entry() for d in used_datasources],
        }

    @classmethod
    async def get_serialized_schema(
        cls, options: Options, datasource: Union[Datasource[Collection], DatasourceCustomizer], meta: AgentMeta
    ):
        meta_v2 = cls.generate_meta(meta, datasource)
        schema_path = f'{options["schema_path"].split(".json")[0]}_v2.json'
        full_schema_path = f'{options["schema_path"].split(".json")[0]}_full_v2.json'
        if not options["is_production"]:
            collections_schema = await SchemaEmitterV2.generate(options["prefix"], datasource)

            with open(full_schema_path, "w", encoding="utf-8") as schema_file:
                json.dump({"collections": collections_schema, "meta": meta_v2}, schema_file, indent=4)

            reduced_collections = []
            for collection in collections_schema:
                reduced_collections.append(template_reduce_collection(collection))
            collections_schema = reduced_collections
            with open(schema_path, "w", encoding="utf-8") as schema_file:
                json.dump({"collections": reduced_collections, "meta": meta_v2}, schema_file, indent=4)
        else:
            1 / 0
            try:
                with open(schema_path, "r", encoding="utf-8") as schema_file:
                    collections_schema = json.load(schema_file)["collections"]

            except Exception:
                ForestLogger.log(
                    "error",
                    f"Can't read {options['schema_path']}. Providing a schema is mandatory in production. Skipping...",
                )
                raise

        return cls.serialize(collections_schema, meta_v2)

    @staticmethod
    async def generate(
        prefix: str, datasource: Union[Datasource[Collection], DatasourceCustomizer]
    ) -> List[SchemaV2Collection]:
        """generate schema from datasource"""
        collection_schema: List[SchemaV2Collection] = []
        for collection in datasource.collections:
            collection_schema.append(await SchemaCollectionGeneratorV2.build(prefix, collection))  # type:ignore
        return sorted(collection_schema, key=lambda collection: collection["name"])


def _get_base_datasource(input_collection: Collection) -> Datasource:
    collection = input_collection

    while isinstance(collection, CollectionDecorator):
        collection = collection.child_collection

    return collection.datasource  # type:ignore
