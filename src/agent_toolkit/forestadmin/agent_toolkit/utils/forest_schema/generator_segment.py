from typing import Union

from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerSegment
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer


class SchemaSegmentGenerator:
    @staticmethod
    async def build(collection: Union[Collection, CollectionCustomizer], name: str) -> ForestServerSegment:
        return {"id": f"{collection.name}.{name}", "name": name}
