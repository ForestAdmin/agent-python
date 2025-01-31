from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union, cast

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.services.serializers import DumpedResult
from forestadmin.agent_toolkit.utils.id import pack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ManyToMany,
    ManyToOne,
    OneToMany,
    OneToOne,
    PolymorphicManyToOne,
    PolymorphicOneToMany,
    PolymorphicOneToOne,
    PrimitiveType,
    RelationAlias,
    StraightRelationAlias,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class JsonApiSerializer:
    def __init__(self, datasource: Datasource, projection: Projection) -> None:
        self.datasource = datasource
        self.projection = projection

    def serialize(self, data, collection: Collection) -> DumpedResult:
        if isinstance(data, list):
            ret = self._serialize_many(data, collection)
        else:
            ret = self._serialize_one(data, collection)

        if ret.get("included") == []:
            del ret["included"]
        return ret

    @classmethod
    def _get_id(cls, collection: Collection, data: RecordsDataAlias) -> Union[int, str]:
        pk = pack_id(collection.schema, data)
        try:
            pk = int(pk)
        except ValueError:
            pass
        return pk

    @classmethod
    def _is_in_included(cls, included: List[Dict[str, Any]], item: Dict[str, Any]) -> bool:
        for included_item in included:
            if included_item["id"] == item["id"] and included_item["type"] == item["type"]:
                return True
        return False

    def _serialize_many(self, data, collection: Collection) -> DumpedResult:
        ret = {"data": [], "included": []}
        for item in data:
            serialized = self._serialize_one(item, collection)
            ret["data"].append(serialized["data"])
            for included in serialized["included"]:
                if not self._is_in_included(ret["included"], included):
                    ret["included"].append(included)

        return ret

    def _serialize_one(self, data: RecordsDataAlias, collection: Collection, projection: Optional[Projection] = None):
        projection = projection if projection is not None else self.projection
        primary_keys = SchemaUtils.get_primary_keys(collection.schema)
        pk_value = self._get_id(collection, data)
        ret = {
            "data": {
                "id": pk_value,
                "attributes": {},
                "links": {"self": f"/forest/{collection.name}/{pk_value}"},
                "relationships": {},
                "type": collection.name,
            },
            "included": [],
            "links": {"self": f"/forest/{collection.name}/{pk_value}"},
        }

        first_level_projection = [*projection.relations.keys(), *projection.columns]
        for key, value in data.items():
            if key in primary_keys or key not in collection.schema["fields"]:
                continue
            if is_column(collection.schema["fields"][key]) and key in first_level_projection:
                ret["data"]["attributes"][key] = self._serialize_value(value, collection.schema["fields"][key])
            elif not is_column(collection.schema["fields"][key]):
                relation, included = self._serialize_relation(
                    key, data, collection.schema["fields"][key], f"/forest/{collection.name}/{pk_value}"
                )
                ret["data"]["relationships"][key] = relation
                if included != {} and not self._is_in_included(ret["included"], included):
                    ret["included"].append(included)

        if ret["data"].get("attributes") == {}:
            del ret["data"]["attributes"]
        return ret

    def _serialize_value(self, value: Any, schema: Column) -> Union[str, int, float, bool, None]:
        if value is None:
            return None
        if schema["column_type"] in [PrimitiveType.STRING, PrimitiveType.NUMBER, PrimitiveType.BOOLEAN]:
            return value
        elif schema["column_type"] in [PrimitiveType.UUID, PrimitiveType.ENUM]:
            return str(value)
        elif schema["column_type"] == PrimitiveType.DATE:
            return cast(datetime, value).isoformat()
        elif schema["column_type"] == PrimitiveType.DATE_ONLY:
            return cast(date, value).isoformat()
        elif schema["column_type"] == PrimitiveType.TIME_ONLY:
            return str(value)  # TODO: validate
        elif schema["column_type"] == PrimitiveType.BINARY:
            return value  # TODO: validate
        elif schema["column_type"] == PrimitiveType.POINT:
            return str(value)  # TODO: validate
        elif schema["column_type"] == PrimitiveType.JSON:
            return value  # TODO: validate
        elif isinstance(schema["column_type"], dict) or isinstance(schema["column_type"], list):
            return value
        else:
            ForestLogger.log("error", f"Unknown column type {schema['column_type']}")
            raise AgentToolkitException(f"Unknown column type {schema['column_type']}")

    def _serialize_relation(
        self, name: str, data: Any, schema: RelationAlias, current_link: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        relation, included = {}, {}
        sub_data = data[name]
        if sub_data is None:
            return {
                "data": None,
                "links": {"related": {"href": f"{current_link}/relationships/{name}"}},
            }, included

        if is_polymorphic_many_to_one(schema):
            relation, included = self._serialize_polymorphic_many_to_one_relationship(name, data, schema, current_link)
        elif is_many_to_one(schema) or is_one_to_one(schema) or is_polymorphic_one_to_one(schema):
            relation, included = self._serialize_to_one_relationships(name, sub_data, schema, current_link)
        elif is_many_to_many(schema) or is_one_to_many(schema):
            relation = {
                "data": [],
                "links": {"related": {"href": f"{current_link}/relationships/{name}"}},
            }

        return relation, included

    def _serialize_to_one_relationships(
        self,
        name: str,
        data: Any,
        schema: Union[PolymorphicOneToOne, OneToOne, ManyToOne],
        current_link: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        foreign_collection = self.datasource.get_collection(schema["foreign_collection"])

        relation = {
            "data": {
                "id": pack_id(foreign_collection.schema, data),
                # "id": self._get_id(foreign_collection, data),
                "type": schema["foreign_collection"],
            },
            "links": {"related": {"href": f"{current_link}/relationships/{name}"}},
        }

        sub_projection = self.projection.relations[name]
        included_attributes = {}
        for key, value in data.items():
            if key not in sub_projection or key in SchemaUtils.get_primary_keys(foreign_collection.schema):
                continue
            included_attributes[key] = self._serialize_value(value, foreign_collection.schema["fields"][key])

        included = {
            "id": self._get_id(foreign_collection, data),
            "links": {
                "self": f"/forest/{foreign_collection.name}/{self._get_id(foreign_collection, data)}",
            },
            "type": foreign_collection.name,
        }
        if included_attributes != {}:
            included["attributes"] = included_attributes
        return relation, included

    def _serialize_polymorphic_many_to_one_relationship(
        self,
        name: str,
        data: Any,
        schema: PolymorphicManyToOne,
        current_link: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        sub_data = data[name]
        foreign_collection = self.datasource.get_collection(data[schema["foreign_key_type_field"]])

        relation = {
            "data": {
                "id": pack_id(foreign_collection.schema, sub_data),  # TODO: validate
                # "id": self._get_id(foreign_collection, sub_data),
                "type": foreign_collection.name,
            },
            "links": {"related": {"href": f"{current_link}/relationships/{name}"}},
        }
        included = self._serialize_one(
            sub_data, foreign_collection, ProjectionFactory.all(foreign_collection, allow_nested=True)
        )
        included = {**included["data"], "links": included["links"], "relationships": {}}

        # add relationships key in included
        for foreign_relation_name, foreign_relation_schema in foreign_collection.schema["fields"].items():
            if not is_column(foreign_relation_schema):
                included["relationships"][foreign_relation_name] = {
                    "links": {
                        "related": {
                            "href": f"/forest/{foreign_collection.name}/{self._get_id(foreign_collection, sub_data)}/relationships/{foreign_relation_name}"
                        }
                    }
                }

        return relation, included
