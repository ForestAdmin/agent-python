from typing import Any

from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class SchemaCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        self.schema_override = {}
        super().__init__(*args, **kwargs)

    def override_schema(self, attribute: str, value: Any):
        self.schema_override[attribute] = value
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        return {**sub_schema, **self.schema_override}
