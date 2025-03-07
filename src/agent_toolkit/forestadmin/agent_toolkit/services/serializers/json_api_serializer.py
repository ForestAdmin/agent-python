from ast import literal_eval
from datetime import date, datetime, time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from uuid import uuid4

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.services.serializers import Data, DumpedResult, IncludedData
from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiSerializerException
from forestadmin.agent_toolkit.utils.id import pack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ManyToOne,
    OneToOne,
    PolymorphicManyToOne,
    PolymorphicOneToOne,
    PrimitiveType,
    RelationAlias,
    is_column,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def render_chart(chart: Chart):
    return {"id": str(uuid4()), "type": "stats", "attributes": {"value": chart}}


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
        return cast(DumpedResult, ret)

    @classmethod
    def _get_id(cls, collection: Collection, data: RecordsDataAlias) -> Union[int, str]:
        pk = pack_id(collection.schema, data)
        try:
            pk = int(pk)
        except ValueError:
            pass
        return pk

    @classmethod
    def _is_in_included(cls, included: List[Dict[str, Any]], item: IncludedData) -> bool:
        if "id" not in item or "type" not in item:
            raise JsonApiSerializerException("Included item must have an id and a type")
        for included_item in included:
            if included_item["id"] == item["id"] and included_item["type"] == item["type"]:
                return True
        return False

    def _serialize_many(self, data, collection: Collection) -> DumpedResult:
        ret = {"data": [], "included": []}
        for item in data:
            serialized = self._serialize_one(item, collection)
            ret["data"].append(serialized["data"])
            for included in serialized.get("included", []):
                if not self._is_in_included(ret["included"], included):
                    ret["included"].append(included)

        return cast(DumpedResult, ret)

    def _serialize_one(
        self, data: RecordsDataAlias, collection: Collection, projection: Optional[Projection] = None
    ) -> DumpedResult:
        projection = projection if projection is not None else self.projection
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
            if key not in first_level_projection or key not in collection.schema["fields"]:
                continue
            if is_column(collection.schema["fields"][key]) and key in first_level_projection:
                ret["data"]["attributes"][key] = self._serialize_value(
                    value, cast(Column, collection.schema["fields"][key])
                )
            elif not is_column(collection.schema["fields"][key]):
                relation, included = self._serialize_relation(
                    key,
                    data,
                    cast(RelationAlias, collection.schema["fields"][key]),
                    f"/forest/{collection.name}/{pk_value}",
                )
                ret["data"]["relationships"][key] = relation
                if included is not None and not self._is_in_included(ret["included"], included):
                    ret["included"].append(included)

        if ret["data"].get("attributes") == {}:
            del ret["data"]["attributes"]
        if ret["data"].get("relationships") == {}:
            del ret["data"]["relationships"]
        return cast(DumpedResult, ret)

    def _serialize_value(self, value: Any, schema: Column) -> Union[str, int, float, bool, None]:
        if value is None:
            return None

        def number_dump(val):
            if isinstance(val, int) or isinstance(val, float):
                return val
            elif isinstance(val, str):
                return literal_eval(str(value))

        parser_map: Dict[PrimitiveType, Callable] = {
            PrimitiveType.STRING: str,
            PrimitiveType.ENUM: str,
            PrimitiveType.BOOLEAN: bool,
            PrimitiveType.NUMBER: number_dump,
            PrimitiveType.UUID: str,
            PrimitiveType.DATE_ONLY: lambda v: v if isinstance(v, str) else date.isoformat(v),
            PrimitiveType.TIME_ONLY: lambda v: v if isinstance(v, str) else time.isoformat(v),
            PrimitiveType.DATE: lambda v: v if isinstance(v, str) else datetime.isoformat(v),
            PrimitiveType.POINT: lambda v: v,
            PrimitiveType.BINARY: lambda v: v,  # should not be called, because of binary decorator this type
            # is transformed to string
            PrimitiveType.JSON: lambda v: v,
        }

        if isinstance(schema["column_type"], PrimitiveType):
            return parser_map[cast(PrimitiveType, schema["column_type"])](value)
        elif isinstance(schema["column_type"], dict) or isinstance(schema["column_type"], list):
            return value
        else:
            ForestLogger.log("error", f"Unknown column type {schema['column_type']}")
            raise JsonApiSerializerException(f"Unknown column type {schema['column_type']}")

    def _serialize_relation(
        self, name: str, data: Any, schema: RelationAlias, current_link: str
    ) -> Tuple[Dict[str, Any], Optional[IncludedData]]:
        relation, included = {}, None
        sub_data = data[name]
        if sub_data is None:
            return {
                "data": (
                    None
                    if is_polymorphic_many_to_one(schema) or is_polymorphic_one_to_one(schema) or is_one_to_one(schema)
                    else []
                ),
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
    ) -> Tuple[Dict[str, Any], IncludedData]:
        """return (relationships, included)"""
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
            if key not in sub_projection:
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
        return relation, cast(IncludedData, included)

    def _serialize_polymorphic_many_to_one_relationship(
        self,
        name: str,
        data: Any,
        schema: PolymorphicManyToOne,
        current_link: str,
    ) -> Tuple[Dict[str, Any], Optional[IncludedData]]:
        """return (relationships, included)"""
        sub_data = data[name]
        try:
            foreign_collection = self.datasource.get_collection(data[schema["foreign_key_type_field"]])
        except DatasourceException:
            return {"data": None, "links": {"related": {"href": f"{current_link}/relationships/{name}"}}}, None

        relation = {
            "data": {
                "id": pack_id(foreign_collection.schema, sub_data),  # TODO: validate
                # "id": self._get_id(foreign_collection, sub_data),
                "type": data[schema["foreign_key_type_field"]],
            },
            "links": {"related": {"href": f"{current_link}/relationships/{name}"}},
        }
        included = self._serialize_one(
            sub_data, foreign_collection, ProjectionFactory.all(foreign_collection, allow_nested=True)
        )
        included["data"] = cast(Data, included["data"])
        included = {
            "type": included["data"]["type"],
            "id": included["data"]["id"],
            "attributes": included["data"]["attributes"],
            # **included.get("data", {}),  # type: ignore for serialize_one it's a dict
            "links": included.get("links", {}),
            "relationships": {},
        }

        # add relationships key in included
        for foreign_relation_name, foreign_relation_schema in foreign_collection.schema["fields"].items():
            if not is_column(foreign_relation_schema):
                included["relationships"][foreign_relation_name] = {
                    "links": {
                        "related": {
                            "href": f"/forest/{foreign_collection.name}/{self._get_id(foreign_collection, sub_data)}"
                            f"/relationships/{foreign_relation_name}"
                        }
                    }
                }

        return relation, cast(IncludedData, included)
