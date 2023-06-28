from typing import Any, Dict, List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldAlias,
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


class PublicationFieldCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        self._unpublished: Dict[str, FieldAlias] = {}
        super().__init__(*args, **kwargs)

    def change_field_visibility(self, name: str, visible: bool):
        if name in self._unpublished and visible:
            self._unpublished.pop(name)
        else:
            field = self.get_field(name)
            if is_column(field) and field.get("is_primary_key", False):
                raise PublicationCollectionException("Cannot hide primary key")
            if not visible:
                self._unpublished[name] = field
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        new_field_schema = {}
        for name, field in sub_schema["fields"].items():
            if self._is_published(name):
                new_field_schema[name] = field
        return {**sub_schema, "fields": new_field_schema}

    def _is_published(self, name: str) -> bool:
        field = self.child_collection.get_field(name)
        return name not in self._unpublished and (
            is_column(field)
            or (
                (is_many_to_one(field) and self._is_published(field["foreign_key"]))
                or (
                    (is_one_to_one(field) or is_one_to_many(field))
                    and self.datasource.get_collection(field["foreign_collection"])._is_published(field["origin_key"])
                )
                or (
                    is_many_to_many(field)
                    and self.datasource.get_collection(field["through_collection"])._is_published(field["foreign_key"])
                    and self.datasource.get_collection(field["through_collection"])._is_published(field["origin_key"])
                )
            )
        )

    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        records = await super().create(caller, data)
        new_records = []
        for record in records:
            tmp_record = {}
            for field_name, field in record.items():
                if field_name not in self._unpublished:
                    tmp_record[field_name] = field
            new_records.append(tmp_record)
        return new_records
