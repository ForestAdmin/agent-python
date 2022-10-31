from typing import Any, Dict, List, Literal, Union

from forestadmin.agent_toolkit.options import AgentMeta, Options
from forestadmin.agent_toolkit.utils.forest_schema.generator_collection import SchemaCollectionGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerCollection
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource import CustomizedDatasource


class SchemaEmitter:
    """
    private static readonly meta = {
           liana: 'forest-nodejs-agent',
           liana_version: version,
           stack: {
           engine: 'nodejs',
           engine_version: process.versions && process.versions.node,
           },
       };

       static async getSerializedSchema(
           options: Options,
           dataSource: DataSource,
       ): Promise<SerializedSchema> {
           const schema: RawSchema = options.isProduction
           ? await SchemaEmitter.loadFromDisk(options.schemaPath)
           : await SchemaEmitter.generate(options.prefix, dataSource);

           if (!options.isProduction) {
           const pretty = stringify(schema, { maxLength: 80 });
           await writeFile(options.schemaPath, pretty, { encoding: 'utf-8' });
           }

           const hash = crypto.createHash('sha1').update(JSON.stringify(schema)).digest('hex');

           return SchemaEmitter.serialize(schema, hash);
       }

       private static async loadFromDisk(schemaPath: string): Promise<RawSchema> {
           try {
           const fileContent = await readFile(schemaPath, { encoding: 'utf-8' });

           return JSON.parse(fileContent);
           } catch (e) {
           throw new Error(
               `Cannot load ${schemaPath}. Providing a schema is mandatory in production mode.`,
           );
           }
       }

       private static async generate(prefix: string, dataSource: DataSource): Promise<RawSchema> {
           const allCollectionSchemas = [];

           const dataSourceCollectionSchemas = dataSource.collections.map(collection =>
           SchemaGeneratorCollection.buildSchema(prefix, collection),
           );
           allCollectionSchemas.push(...dataSourceCollectionSchemas);

           return Promise.all(allCollectionSchemas);
       }

       private static serialize(schema: RawSchema, hash: string): SerializedSchema {
           // Build serializer
           const serializer = new JSONAPISerializer();

           serializer.register('collections', {
           // Pass the metadata provided to the serialization fn
           topLevelMeta: (extraData: unknown) => extraData,
           relationships: {
               segments: { type: 'segments' },
               actions: { type: 'actions' },
           },
           });
           serializer.register('segments', {});
           serializer.register('actions', {});

           // Serialize
           return serializer.serialize(
           'collections',
           schema.map(c => ({ id: c.name, ...c })),
           { ...SchemaEmitter.meta, schemaFileHash: hash },
           ) as SerializedSchema;
       }
       static async getSerializedSchema(
           options: Options,
           dataSource: DataSource,
       ): Promise<SerializedSchema> {
           const schema: RawSchema = options.isProduction
           ? await SchemaEmitter.loadFromDisk(options.schemaPath)
           : await SchemaEmitter.generate(options.prefix, dataSource);

           if (!options.isProduction) {
           const pretty = stringify(schema, { maxLength: 80 });
           await writeFile(options.schemaPath, pretty, { encoding: 'utf-8' });
           }

           const hash = crypto.createHash('sha1').update(JSON.stringify(schema)).digest('hex');

           return SchemaEmitter.serialize(schema, hash);
       }
       for collection in copy.deepcopy(cls.schema_data['collections']):
           actions_data, actions_included = cls.get_serialized_collection_relation(collection, 'actions')
           segments_data, segments_included = cls.get_serialized_collection_relation(collection, 'segments')
           c = {
               'id': collection['name'],
               'type': 'collections',
               'attributes': cls.get_serialized_collection(collection),
               'relationships': {
                   'actions': {
                       'data': actions_data
                   },
                   'segments': {
                       'data': segments_data
                   }
               }
           }
           data.append(c)
           included.extend(actions_included)
           included.extend(segments_included)

       return {
           'data': data,
           'included': included,
           'meta': cls.schema_data['meta']
       }
    """

    @staticmethod
    def get_serialized_collection_relation(
        collection: ForestServerCollection, rel_type: Literal["actions", "segments"]
    ):
        data: List[Dict[str, str]] = []
        included: List[Dict[str, str]] = []
        for rel in collection.get(rel_type, []):
            id = f"{collection['name']}.{rel['name']}"
            data.append({"id": id, "type": rel_type})
            included.append({"id": id, "type": rel_type, "attributes": rel})
        return data, included

    @classmethod
    def serialize(cls, collections: List[ForestServerCollection], meta: AgentMeta) -> Dict[str, Any]:
        serialized_collections: List[Dict[str, Any]] = []
        included: List[Dict[str, str]] = []
        for collection in collections:
            action_data, action_included = cls.get_serialized_collection_relation(collection, "actions")
            included.extend(action_included)
            segments = collection.pop("segments")
            serialized_collections.append(
                {
                    "id": collection["name"],
                    "type": "collections",
                    "attributes": collection,
                    "relationships": {"actions": {"data": action_data}, "segments": {"data": segments}},
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
