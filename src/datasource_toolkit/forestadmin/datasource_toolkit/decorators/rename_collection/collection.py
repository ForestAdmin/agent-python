from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import is_column, is_many_to_many, is_polymorphic_many_to_one
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema


class RenameCollectionCollectionDecorator(CollectionDecorator):
    @property
    def name(self) -> str:
        return self.datasource.get_collection_name(super().name)

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields = {}

        for name, old_schema in sub_schema["fields"].items():
            schema = {**old_schema}

            if not is_column(schema) and not is_polymorphic_many_to_one(schema):
                schema["foreign_collection"] = self.datasource.get_collection_name(schema["foreign_collection"])
                if is_many_to_many(schema):
                    schema["through_collection"] = self.datasource.get_collection_name(schema["through_collection"])
            fields[name] = schema

        return {**sub_schema, "fields": fields}
