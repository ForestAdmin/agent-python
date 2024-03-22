from typing import Any, List, Set

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException, ForestException
from forestadmin.datasource_toolkit.interfaces.fields import (
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class PublicationCollectionException(DatasourceToolkitException):
    pass


class PublicationCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        self._blacklist: Set[str] = set()
        super().__init__(*args, **kwargs)

    def change_field_visibility(self, name: str, visible: bool):
        """Show/hide fields from the schema"""
        field = self.child_collection.schema["fields"].get(name)
        if field is None:
            available_fields = [field_name for field_name in self.child_collection.schema["fields"].keys()]
            raise ForestException(f"No such field '{self.name}.{name}', choices are {', '.join(available_fields)}")

        if is_column(field) and field.get("is_primary_key", False):
            raise ForestException("Cannot hide primary key")

        if visible is False:
            self._blacklist.add(name)
        elif visible is True and name in self._blacklist:
            self._blacklist.remove(name)

        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        new_field_schema = {}
        for name, field in sub_schema["fields"].items():
            if self._is_published(name):
                new_field_schema[name] = field
        return {**sub_schema, "fields": new_field_schema}

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        records = await super().create(caller, data)
        return [{key: value for key, value in record.items() if key not in self._blacklist} for record in records]

    def _is_published(self, name: str) -> bool:
        # explicit hidden
        if name in self._blacklist:
            return False

        # implicit hidden
        field = self.child_collection.get_field(name)

        if is_many_to_one(field):
            return (
                self.datasource.is_published(field["foreign_collection"])
                and self._is_published(field["foreign_key"])
                and self.datasource.get_collection(field["foreign_collection"])._is_published(
                    field["foreign_key_target"]
                )
            )

        if is_one_to_one(field) or is_one_to_many(field):
            return (
                self.datasource.is_published(field["foreign_collection"])
                and self.datasource.get_collection(field["foreign_collection"])._is_published(field["origin_key"])
                and self._is_published(field["origin_key_target"])
            )

        if is_many_to_many(field):
            return (
                self.datasource.is_published(field["through_collection"])
                and self.datasource.is_published(field["foreign_collection"])
                and self.datasource.get_collection(field["through_collection"])._is_published(field["foreign_key"])
                and self.datasource.get_collection(field["through_collection"])._is_published(field["origin_key"])
                and self._is_published(field["origin_key_target"])
                and self.datasource.get_collection(field["foreign_collection"])._is_published(
                    field["foreign_key_target"]
                )
            )

        return True
