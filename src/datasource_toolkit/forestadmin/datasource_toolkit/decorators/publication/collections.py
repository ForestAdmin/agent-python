from typing import Any, Callable, Dict

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


class PublicationCollectionException(DatasourceToolkitException):
    pass


class PublicationMixin:

    datasource: property
    mark_schema_as_dirty: Callable[..., None]
    get_field: Callable[[str], Any]

    def __init__(self, *args: Any, **kwargs: Any):
        super(PublicationMixin, self).__init__(*args, **kwargs)
        self._unpublished: Dict[str, FieldAlias] = {}
        self._republished_fields: Dict[str, FieldAlias] = {}

    def change_field_visibility(self, name: str, visible: bool):
        if name in self._unpublished and visible:
            self._republished_fields[name] = self._unpublished.pop(name)
        else:
            field = self.get_field(name)
            if is_column(field) and field["is_primary_key"]:
                raise PublicationCollectionException("Cannot hide primary key")
            if not visible:
                self._unpublished[name] = field
        self.mark_schema_as_dirty()

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(PublicationMixin, self).schema  # type: ignore
        new_field_schema = {}
        for name, field in schema["fields"].items():
            if self._is_published(name):
                new_field_schema[name] = field
        for name, field in self._republished_fields.items():
            new_field_schema[name] = field
        self._republished_fields = {}
        schema["fields"] = new_field_schema
        return schema

    def _is_published(self, name: str) -> bool:
        field = self.get_field(name)
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
