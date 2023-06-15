from typing import Any

from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class SchemaMixin:
    def __init__(self, *args: Any, **kwargs: Any):
        self.schema_override = {}
        super(SchemaMixin, self).__init__(*args, **kwargs)

    def override_schema(self, attribute: str, value: Any):
        self.schema_override[attribute] = value
        self.mark_schema_as_dirty()

    def _refine_schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(SchemaMixin, self)._refine_schema()
        schema.update(self.schema_override)
        return schema
