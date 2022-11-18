from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, cast

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.utils.id import pack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
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

CollectionAlias = Union[Collection, CustomizedCollection]


class IntOrFloat(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):  # type: ignore
        if value is None:
            return value
        try:
            return int(value)
        except ValueError:
            return float(value)

    def _deserialize(self, value, attr, data, **kwargs):  # type: ignore
        if value is None:
            return value
        try:
            return int(value)
        except ValueError:
            return float(value)


def schema_name(collection: CollectionAlias):
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


def _create_relationship(collection: CollectionAlias, field_name: str, relation: RelationAlias):
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


def _create_schema_attributes(collection: CollectionAlias) -> Dict[str, Any]:
    attributes: Dict[str, Any] = {}

    for name, field_schema in collection.schema["fields"].items():
        if is_column(field_schema):
            attributes[name] = _map_attribute_to_marshmallow(field_schema["column_type"])
        else:
            attributes[name] = _create_relationship(collection, name, cast(RelationAlias, field_schema))
    if "id" not in attributes:
        attributes["id"] = fields.Str()
    return attributes


class JsonApiSerializer(type):

    schema: Dict[str, Type["ForestSchema"]] = {}
    attributes: Dict[str, Any] = {}

    def __new__(cls: Any, collection_name: str, bases: Tuple[Any], attrs: Dict[str, Any]):
        cls.attributes[collection_name] = attrs.copy()  # attrs is removed by the parent init
        klass = super(JsonApiSerializer, cls).__new__(cls, collection_name, bases, attrs)
        cls.schema[collection_name] = klass
        return klass

    @classmethod
    def get(cls, collection: CollectionAlias) -> Type["ForestSchema"]:
        json_schema_name = schema_name(collection)
        try:
            json_schema = cls.schema[json_schema_name]
        except KeyError:
            raise JsonApiException(f"The serializer for the collection {collection.name} is not built")

        current_attr = _create_schema_attributes(collection)

        if cls.attributes[json_schema_name].keys() != current_attr.keys():
            json_schema = refresh_json_api_schema(collection)
        return json_schema  # type: ignore


class JsonApiSchemaType(JsonApiSerializer, SchemaMeta):
    pass


class ForestRelationShip(fields.Relationship):
    def __init__(self, *args, **kwargs):  # type: ignore
        self.collection: Collection = kwargs.pop("collection")  # type: ignore
        self.related_collection: Collection = self.collection.datasource.get_collection(kwargs["type_"])  # type: ignore
        super(ForestRelationShip, self).__init__(*args, **kwargs)  # type: ignore

    @property
    def schema(self) -> "ForestSchema":
        SchemaClass: Type[Schema] = JsonApiSerializer.get(self.related_collection)
        return SchemaClass(
            only=getattr(self, "only", None), exclude=getattr(self, "exclude", ()), context=getattr(self, "context", {})
        )

    def get_related_url(self, obj: Any):
        if "data" in obj:
            obj["__forest_id__"] = obj["data"]["id"]
        else:
            obj["__forest_id__"] = obj["id"]
        res: Any = super(ForestRelationShip, self).get_related_url(obj)  # type: ignore
        del obj["__forest_id__"]
        return res


class ForestSchema(Schema):
    def __init__(self, *args, **kwargs):  # type: ignore
        if "projections" in kwargs:
            only, include_data = self._build_only_included_data(kwargs.pop("projections"))  # type: ignore
            kwargs["only"] = only
            if "include_data" not in kwargs:
                kwargs["include_data"] = include_data
        super(ForestSchema, self).__init__(*args, **kwargs)  # type: ignore

    def _build_only_included_data(self, projections: Projection):
        only: Set[str] = set()
        include_data: Set[str] = set()
        for projection in cast(List[str], projections):
            if ":" in projection:
                only.add(projection.replace(":", "."))
                include_data.add(projection.split(":")[0])
            else:
                only.add(projection)
        if "id" not in only:
            only.add("id")
        return only, include_data

    def get_resource_links(self, item: Any):
        item["__forest_id__"] = pack_id(self.Meta.fcollection.schema, item)  # type: ignore
        res = super(ForestSchema, self).get_resource_links(item)  # type: ignore
        del item["__forest_id__"]
        return res

    def _populate_id(self, obj: Union[Dict[str, Any], List[Dict[str, Any]]]):
        if isinstance(obj, list):
            for o in obj:
                self._populate_id(o)
        elif "id" not in obj:
            obj["id"] = pack_id(self.Meta.fcollection.schema, obj)  # type: ignore
        return obj

    def dump(self, obj: Any, *, many: Optional[bool] = None) -> Any:
        self._populate_id(obj)
        try:
            res = super().dump(obj, many=many)  # type: ignore
        except MarshmallowError as e:
            raise JsonApiException(str(e))
        return res  # type: ignore

    def load(self, data, *, many=None, partial=None, unknown=None):  # type: ignore

        try:
            return super().load(data, many=many, partial=partial, unknown=unknown)  # type: ignore
        except MarshmallowError as e:
            raise JsonApiException(str(e))

    def unwrap_item(self, item):  # type: ignore
        # needed to avoid an issue introduced by the front (type are pluralize for add and update)
        item["type"] = self.opts.type_  # type: ignore
        for name, relationship in item.get("relationships", {}).items():  # type: ignore
            relation_field = self.Meta.fcollection.get_field(name)  # type: ignore
            relationship["data"]["type"] = relation_field["foreign_collection"]  # type: ignore
            item["relationships"][name] = relationship
        return super(ForestSchema, self).unwrap_item(item)  # type: ignore


def refresh_json_api_schema(collection: CollectionAlias, ignores: Optional[List[CollectionAlias]] = None):

    if ignores is None:
        ignores = []
    if collection in ignores:
        return
    ignores.append(collection)
    if schema_name(collection) not in JsonApiSerializer.schema:
        raise JsonApiException("The schema doesn't exist")
    del JsonApiSerializer.schema[schema_name(collection)]
    return create_json_api_schema(collection)


def create_json_api_schema(collection: CollectionAlias):
    if schema_name(collection) in JsonApiSerializer.schema:
        raise JsonApiException("The schema has already been created for this collection")

    attributes: Dict[str, Any] = _create_schema_attributes(collection)

    class JsonApiSchema(ForestSchema):
        class Meta:  # type: ignore
            type_ = collection.name
            self_url = f"/forest/{collection.name}/{{{collection.name.lower()}_id}}"
            self_url_kwargs = {f"{collection.name.lower()}_id": "<__forest_id__>"}
            strict = True
            fcollection: CollectionAlias = collection

    return JsonApiSchemaType(schema_name(collection), (JsonApiSchema,), attributes)
