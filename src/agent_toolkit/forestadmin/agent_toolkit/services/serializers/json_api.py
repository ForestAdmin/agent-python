from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, cast
from uuid import uuid4

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.id import pack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldAlias,
    Operator,
    PolymorphicManyToOne,
    PrimitiveType,
    RelationAlias,
    is_column,
    is_many_to_many,
    is_one_to_many,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from marshmallow.exceptions import MarshmallowError
from marshmallow.schema import SchemaMeta
from marshmallow_jsonapi import Schema, fields  # type: ignore

CollectionAlias = Union[Collection, CollectionCustomizer]


class IntOrFloat(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):  # type: ignore
        if value is None:
            return value
        if isinstance(value, int) or isinstance(value, float):
            return value
        try:
            return int(value)
        except ValueError:
            return float(value)

    def _deserialize(self, value, attr, data, **kwargs):  # type: ignore
        if value is None:
            return value
        if isinstance(value, int) or isinstance(value, float):
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


def _map_attribute_to_marshmallow(column_alias: FieldAlias):
    if isinstance(column_alias["column_type"], PrimitiveType):
        type_ = _map_primitive_type(column_alias["column_type"])
    else:
        type_ = fields.Raw

    is_nullable = column_alias.get("is_read_only", False) is True or (
        column_alias.get("validations") is not None
        and {"operator": Operator.PRESENT} not in column_alias["validations"]
    )
    return type_(allow_none=is_nullable)


def _create_relationship(collection: CollectionAlias, field_name: str, relation: RelationAlias):
    many = is_one_to_many(relation) or is_many_to_many(relation) or is_polymorphic_one_to_many(relation)
    kwargs = {
        "many": many,
        "related_url": f"/forest/{collection.name}/{{{collection.name.lower()}_id}}/relationships/{field_name}",
        "related_url_kwargs": {f"{collection.name.lower()}_id": "<__forest_id__>"},
        "collection": collection,
        "forest_is_polymorphic": False,
    }
    if is_many_to_many(relation):
        type_ = relation["foreign_collection"]
        kwargs["id_field"] = SchemaUtils.get_primary_keys(collection.datasource.get_collection(type_).schema)[0]
    elif is_polymorphic_many_to_one(relation):
        kwargs["forest_is_polymorphic"] = True
        kwargs["forest_relation"] = relation
        type_ = relation["foreign_collections"]
    else:
        type_ = relation["foreign_collection"]
        kwargs["id_field"] = SchemaUtils.get_primary_keys(collection.datasource.get_collection(type_).schema)[0]
    kwargs.update(
        {
            "type_": type_,
            "schema": f"{type_}_schema",
        }
    )
    return ForestRelationShip(**kwargs)


def _create_schema_attributes(collection: CollectionAlias) -> Dict[str, Any]:
    attributes: Dict[str, Any] = {}
    pks = SchemaUtils.get_primary_keys(collection.schema)
    pk_field = pks[0]
    attributes["id_field"] = pk_field
    attributes["default_id_field"] = pk_field

    for name, field_schema in collection.schema["fields"].items():
        if is_column(field_schema):
            attributes[name] = _map_attribute_to_marshmallow(field_schema)
        else:
            attributes[name] = _create_relationship(collection, name, cast(RelationAlias, field_schema))
    if "id" not in attributes:
        attributes["id"] = _map_primitive_type(collection.get_field(pk_field)["column_type"])()
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
        self.related_collection_name = kwargs["type_"]
        self.forest_is_polymorphic = kwargs.pop("forest_is_polymorphic", None)
        self.forest_relation = kwargs.pop("forest_relation", None)
        self._forest_current_obj = None
        super(ForestRelationShip, self).__init__(*args, **kwargs)  # type: ignore

    @property
    def schema(self) -> "ForestSchema":
        if self.forest_is_polymorphic:
            target_collection_field = cast(PolymorphicManyToOne, self.forest_relation)["foreign_key_type_field"]
            target_collection = self._forest_current_obj[target_collection_field]
            related_collection = self.collection.datasource.get_collection(target_collection)
        else:
            related_collection = self.collection.datasource.get_collection(self.related_collection_name)

        SchemaClass: Type[Schema] = JsonApiSerializer.get(related_collection)
        return SchemaClass(
            only=getattr(self, "only", None), exclude=getattr(self, "exclude", ()), context=getattr(self, "context", {})
        )

    def handle_polymorphism(self, attr):
        target_collection_field = cast(PolymorphicManyToOne, self.forest_relation)["foreign_key_type_field"]
        target_collection = self._forest_current_obj[target_collection_field]

        if target_collection is not None and (
            target_collection not in self.forest_relation["foreign_collections"]
            or target_collection not in [c.name for c in self.collection.datasource.collections]
        ):
            ForestLogger.log(
                "warning",
                f"Trying to serialize a polymorphic relationship ({self.collection.name}.{attr} for record "
                f"{self._forest_current_obj['id']}) of type {target_collection}; but this type is not known by forest."
                " Ignoring and setting this relationship to None.",
            )
            self._forest_current_obj[attr] = None

        self.type_ = target_collection
        if getattr(self, "only", False):
            self._old_only = self.only
            self.only = None

    def teardown_polymorphism(self):
        self.__schema = None  # this is a cache variable, so it's preferable to clean it after
        if getattr(self, "only", False):
            self.only = self._old_only

    def serialize(self, attr, obj, accessor=None):
        self._forest_current_obj = obj
        if self.forest_is_polymorphic:
            self.handle_polymorphism(attr)
        ret = super(ForestRelationShip, self).serialize(attr, obj, accessor)
        if self.forest_is_polymorphic:
            self.teardown_polymorphism()
        return ret

    def _get_id(self, value):
        if self.forest_is_polymorphic:
            type_field = self.forest_relation["foreign_key_type_field"]
            type_value = self._forest_current_obj[type_field]
            return value.get(
                self.forest_relation["foreign_key_targets"][type_value],
                value,
            )
        else:
            return super()._get_id(value)

    def get_related_url(self, obj: Any):
        if "id" in obj:
            obj["__forest_id__"] = obj["id"]
        elif "data" in obj:
            obj["__forest_id__"] = obj["data"]["id"]
        else:
            raise JsonApiException("Cannot find json api 'id' in given obj.")
        res: Any = super(ForestRelationShip, self).get_related_url(obj)  # type: ignore
        del obj["__forest_id__"]
        return {"href": res}


class ForestSchema(Schema):
    def __init__(self, *args, **kwargs):  # type: ignore
        if "projections" in kwargs:
            only, include_data = self._build_only_included_data(kwargs.pop("projections"))  # type: ignore
            kwargs["only"] = only
            if "include_data" not in kwargs:
                kwargs["include_data"] = include_data
        if kwargs.get("only") is not None and "id" not in kwargs["only"]:
            kwargs["only"].add("id")
        super(ForestSchema, self).__init__(*args, **kwargs)  # type: ignore

    def _build_only_included_data(self, projections: Projection):
        only: Set[str] = set()
        include_data: Set[str] = set()
        for projection in cast(List[str], projections):
            if ":" in projection:
                only.add(projection.replace(":*", "").replace(":", "."))
                include_data.add(projection.split(":")[0])
            else:
                only.add(projection)
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
            return obj
        if "id" not in obj:
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
        """needed to avoid an issue introduced by the front (type are pluralize for add and update)"""
        relationship_to_del = []
        item["type"] = self.opts.type_  # type: ignore

        for name, relationships in item.get("relationships", {}).items():
            relation_field = self.Meta.fcollection.get_field(name)  # type: ignore

            if isinstance(relationships["data"], list):
                # for many to many and one to many relations
                for relationship_data in relationships["data"]:
                    relationship_data["type"] = relation_field["foreign_collection"]
            else:
                # for many to one and one to one relations
                if relationships is None or relationships.get("data") in [None, {}]:
                    relationship_to_del.append(name)
                    continue

                # if polymorphic is sent in relationships, lets put the relation in the attributes
                if is_polymorphic_many_to_one(relation_field):
                    item["attributes"][relation_field["foreign_key"]] = relationships["data"]["id"]
                    item["attributes"][relation_field["foreign_key_type_field"]] = relationships["data"]["type"]
                    relationship_to_del.append(name)
                else:
                    relationships["data"]["type"] = relation_field["foreign_collection"]  # type: ignore
                    item["relationships"][name] = relationships

        for name in relationship_to_del:
            del item["relationships"][name]
        return super(ForestSchema, self).unwrap_item(item)


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


def render_chart(chart: Chart):
    return {"id": str(uuid4()), "type": "stats", "attributes": {"value": chart}}
