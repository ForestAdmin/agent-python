from datetime import date, datetime, time
from typing import Any, Callable, Dict, Union, cast
from uuid import UUID

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.services.serializers import Data, DumpedResult
from forestadmin.agent_toolkit.services.serializers.exceptions import JsonApiDeserializerException
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    PrimitiveType,
    is_many_to_many,
    is_many_to_one,
    is_one_to_many,
    is_one_to_one,
    is_polymorphic_many_to_one,
    is_polymorphic_one_to_many,
    is_polymorphic_one_to_one,
)
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class JsonApiDeserializer:
    def __init__(self, datasource: Datasource) -> None:
        self.datasource = datasource

    def deserialize(self, data: DumpedResult, collection: Collection) -> RecordsDataAlias:
        ret = {}
        data["data"] = cast(Data, data["data"])

        for key, value in data["data"]["attributes"].items():
            if key not in collection.schema["fields"]:
                raise JsonApiDeserializerException(f"Field {key} doesn't exists in collection {collection.name}.")
            ret[key] = self._deserialize_value(value, cast(Column, collection.schema["fields"][key]))

        # PK is never sent to deserialize. It's used to identify record. No need to handle it.
        # If it's sent to update the PK value, the new value is in 'attributes'

        for key, value in data["data"].get("relationships", {}).items():
            if key not in collection.schema["fields"]:
                raise JsonApiDeserializerException(f"Field {key} doesn't exists in collection {collection.name}.")
            schema = collection.schema["fields"][key]

            if is_one_to_many(schema) or is_many_to_many(schema) or is_polymorphic_one_to_many(schema):
                raise JsonApiDeserializerException("We shouldn't deserialize toMany relations")

            if value.get("data") is None or "id" not in value["data"]:
                ret[key] = None
                continue

            if is_polymorphic_many_to_one(schema):
                ret[schema["foreign_key_type_field"]] = self._deserialize_value(
                    value["data"]["type"], cast(Column, collection.schema["fields"][schema["foreign_key_type_field"]])
                )
                ret[schema["foreign_key"]] = self._deserialize_value(
                    value["data"]["id"], cast(Column, collection.schema["fields"][schema["foreign_key"]])
                )
                continue

            elif is_many_to_one(schema):
                ret[key] = self._deserialize_value(
                    value["data"]["id"], cast(Column, collection.schema["fields"][schema["foreign_key"]])
                )
            elif is_one_to_one(schema):
                ret[key] = self._deserialize_value(
                    value["data"]["id"], cast(Column, collection.schema["fields"][schema["origin_key_target"]])
                )
            elif is_polymorphic_one_to_one(schema):
                ret[key] = self._deserialize_value(
                    value["data"]["id"], cast(Column, collection.schema["fields"][schema["origin_key_target"]])
                )
        return ret

    def _deserialize_value(self, value: Union[str, int, float, bool, None], schema: Column) -> Any:
        if value is None:
            return None

        def number_parser(val):
            if isinstance(val, int) or isinstance(val, float):
                return val
            try:
                return int(value)
            except ValueError:
                return float(value)

        parser_map: Dict[PrimitiveType, Callable] = {
            PrimitiveType.STRING: str,
            PrimitiveType.ENUM: str,
            PrimitiveType.BOOLEAN: bool,
            PrimitiveType.NUMBER: number_parser,
            PrimitiveType.UUID: lambda v: UUID(v) if isinstance(v, str) else v,
            PrimitiveType.DATE_ONLY: lambda v: date.fromisoformat(v) if isinstance(v, str) else v,
            PrimitiveType.TIME_ONLY: lambda v: time.fromisoformat(v) if isinstance(v, str) else v,
            PrimitiveType.DATE: lambda v: datetime.fromisoformat(v) if isinstance(v, str) else v,
            PrimitiveType.POINT: lambda v: [int(v_) for v_ in cast(str, v).split(",")],
            PrimitiveType.BINARY: lambda v: v,  # should not be called
            PrimitiveType.JSON: lambda v: v,
        }

        if isinstance(schema["column_type"], PrimitiveType):
            return parser_map[cast(PrimitiveType, schema["column_type"])](value)
        elif isinstance(schema["column_type"], dict) or isinstance(schema["column_type"], list):
            return value
        else:
            ForestLogger.log("error", f"Unknown column type {schema['column_type']}")
            raise JsonApiDeserializerException(f"Unknown column type {schema['column_type']}")
