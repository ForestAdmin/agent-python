from typing import Set

from forestadmin.datasource_toolkit.decorators.collections import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    CollectionSchema,
    Datasource,
)
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class PublicationCollectionException(DatasourceToolkitException):
    pass


class PublicationCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource["PublicationCollectionDecorator"]):
        super().__init__(collection, datasource)
        self._unpublished: Set[str] = set()

    def change_field_visibility(self, name: str, visible: bool):
        try:
            field = self.child_collection.schema["fields"][name]
        except KeyError:
            raise PublicationCollectionException(f"No such field '{name}'")

        if is_column(field) and field["is_primary_key"]:
            raise PublicationCollectionException("Cannot hide primary key")

        if not visible:
            self._unpublished.add(name)
        else:
            self._unpublished.remove(name)
        self.mark_schema_as_dirty()

    def is_published(self, name: str) -> bool:
        try:
            field = self.child_collection.schema["fields"][name]
        except KeyError:
            raise PublicationCollectionException(f"No such field '{name}'")

        return name not in self._unpublished and (
            is_column(field)
            or (
                (is_many_to_one(field) and self.is_published(field["foreign_key"]))
                or (
                    (is_one_to_one(field) or is_one_to_many(field))
                    and self.datasource.get_collection(field["foreign_collection"]).is_published(field["origin_key"])
                )
                or (
                    is_many_to_many(field)
                    and self.datasource.get_collection(field["through_collection"]).is_published(field["foreign_key"])
                    and self.datasource.get_collection(field["through_collection"]).is_published(field["origin_key"])
                )
            )
        )

    def _refine_schema(self, child_schema: CollectionSchema) -> CollectionSchema:
        fields: RecordsDataAlias = {}
        for name, field in child_schema["fields"].items():
            if self.is_published(name):
                fields[name] = field

        schema = child_schema.copy()
        schema["fields"] = fields

        return schema
