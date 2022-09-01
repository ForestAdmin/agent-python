from typing import Any, Dict, Optional, Set, Tuple, cast

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.utils.id import pack_id, unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    ColumnAlias,
    PrimitiveType,
    RelationAlias,
    is_column,
    is_many_to_many,
    is_one_to_many,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from marshmallow.exceptions import MarshmallowError
from marshmallow.schema import SchemaMeta
from marshmallow_jsonapi import Schema, fields  # type: ignore


class IntOrFloat(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):  # type: ignore
        if value is None:
            return value
        try:
            return int(value)
        except ValueError:
            return float(value)

    def _deserialize(self, value, attr, data, **kwargs):  # type: ignore
        return value


def schema_name(collection: Collection):
    return f"{collection.name.lower()}_schema"


class JsonApiException(AgentToolkitException):
    pass


def _map_primitive_type(_type: PrimitiveType):
    TYPES = {
        PrimitiveType.STRING: fields.Str,
        PrimitiveType.NUMBER: IntOrFloat,
        PrimitiveType.BOOLEAN: fields.Boolean,
        PrimitiveType.DATE_ONLY: fields.Date,
        PrimitiveType.DATE: fields.DateTime,
        PrimitiveType.TIME_ONLY: fields.Time,
        PrimitiveType.JSON: fields.Raw,
    }
    return TYPES.get(_type, fields.Str)


def _map_attribute_to_marshmallow(column_alias: ColumnAlias):
    if isinstance(column_alias, PrimitiveType):
        return _map_primitive_type(column_alias)()
    elif isinstance(column_alias, list):
        return fields.List
    else:
        return fields.Raw


def _create_relationship(collection: Collection, field_name: str, relation: RelationAlias):
    many = is_one_to_many(relation) or is_many_to_many(relation)
    if is_many_to_many(relation):
        type_ = relation["through_collection"].lower()
    else:
        type_ = relation["foreign_collection"].lower()

    return ForestRelationShip(
        type_=type_,
        many=many,
        schema=f"{type_}_schema",
        related_url=f"/forest/{collection.name}/{{{collection.name.lower()}_id}}/relationships/{field_name}",
        related_url_kwargs={f"{collection.name.lower()}_id": "<__forest_id__>"},
        collection=collection,
    )


def _create_schema_attributes(collection: Collection) -> Dict[str, Any]:
    attributes: Dict[str, Any] = {}
    for name, field_schema in collection.schema["fields"].items():
        if is_column(field_schema):
            attributes[name] = _map_attribute_to_marshmallow(field_schema["column_type"])
        else:
            attributes[name] = _create_relationship(collection, name, cast(RelationAlias, field_schema))
    return attributes


class JsonApiSerializer(type):

    schema: Dict[str, Any] = {}

    def __new__(cls: Any, collection_name: str, bases: Tuple[Any], attrs: Dict[str, Any]):
        klass = super(JsonApiSerializer, cls).__new__(cls, collection_name, bases, attrs)
        cls.schema[collection_name] = klass
        return klass

    @classmethod
    def get(cls, collection: Collection):
        try:
            return cls.schema[schema_name(collection)]
        except KeyError:
            raise JsonApiException(f"The serializer for the collection {collection.name} is not built")


class JsonApiSchemaType(JsonApiSerializer, SchemaMeta):
    pass


class ForestRelationShip(fields.Relationship):
    def __init__(self, *args, **kwargs):  # type: ignore
        try:
            self.collection: Collection = kwargs.pop("collection")  # type: ignore
        except KeyError:
            raise Exception()
        super(ForestRelationShip, self).__init__(*args, **kwargs)  # type: ignore

    def get_related_url(self, obj: Any):
        obj["__forest_id__"] = pack_id(self.collection.schema, obj)
        res: Any = super(ForestRelationShip, self).get_related_url(obj)  # type: ignore
        del obj["__forest_id__"]
        return res

    def _deserialize(self, value, attr, obj, **kwargs):  # type: ignore
        type_: str = obj[attr]["data"]["type"]
        foreign_collection = self.collection.datasource.get_collection(type_)
        pks: str = super()._deserialize(value, attr, obj, **kwargs)  # type: ignore
        return unpack_id(foreign_collection.schema, str(pks))


class ForestSchema(Schema):
    def __init__(self, *args, **kwargs):  # type: ignore
        if "projections" in kwargs:
            only, include_data = self._build_only_included_data(kwargs.pop("projections"))  # type: ignore
            kwargs["only"] = only
            kwargs["include_data"] = include_data
        super(ForestSchema, self).__init__(*args, **kwargs)  # type: ignore

    def _build_only_included_data(self, projections: Projection):
        only: Set[str] = set()
        include_data: Set[str] = set()
        for projection in projections:
            if ":" in projection:
                only.add(projection.replace(":", "."))
                include_data.add(projection.split(":")[0])
            else:
                only.add(projection)
        return only, include_data

    def get_resource_links(self, item: Any):
        item["__forest_id__"] = pack_id(self.Meta.fcollection.schema, item)  # type: ignore
        res = super(ForestSchema, self).get_resource_links(item)  # type: ignore
        del item["__forest_id__"]
        return res

    def dump(self, obj: Any, *, many: Optional[bool] = None) -> Any:
        try:
            return super().dump(obj, many=many)  # type: ignore
        except MarshmallowError as e:
            raise JsonApiException(str(e))

    def load(self, data, *, many=None, partial=None, unknown=None):  # type: ignore
        try:
            return super().load(data, many=many, partial=partial, unknown=unknown)  # type: ignore
        except MarshmallowError as e:
            raise JsonApiException(str(e))


def create_json_api_schema(collection: Collection):
    if schema_name(collection) in JsonApiSerializer.schema:
        raise JsonApiException("The schema has already been created for this collection")
    attrs = _create_schema_attributes(collection)

    class JsonApiSchema(ForestSchema):
        class Meta:  # type: ignore
            type_ = collection.name
            self_url = f"/forest/{collection.name}/{{{collection.name.lower()}_id}}"
            self_url_kwargs = {f"{collection.name.lower()}_id": "<__forest_id__>"}
            strict = True
            fcollection = collection

    res = JsonApiSchemaType(schema_name(collection), (JsonApiSchema,), attrs)
    return res
