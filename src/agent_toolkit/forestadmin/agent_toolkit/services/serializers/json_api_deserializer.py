from datetime import date, datetime, time
from typing import Any, Callable, Dict, Union, cast
from uuid import UUID

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.services.serializers import Data, DumpedResult
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType, is_one_to_one
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class JsonApiDeserializer:
    def __init__(self, datasource: Datasource) -> None:
        self.datasource = datasource

    def deserialize(self, data: DumpedResult, collection: Collection) -> RecordsDataAlias:
        ret = {}
        data["data"] = cast(Data, data["data"])

        for key, value in data["data"]["attributes"].items():
            ret[key] = self._deserialize_value(value, cast(Column, collection.schema["fields"][key]))

        # TODO: relationships
        for key, value in data["data"].get("relationships", {}).items():
            try:
                ret[key] = int(value["data"]["id"])
            except ValueError:
                ret[key] = value["data"]["id"]

        return ret

    def _deserialize_value(self, value: Union[str, int, float, bool, None], schema: Column) -> Any:
        if value is None:
            return None

        def number_parser(val):
            try:
                return int(value)
            except ValueError:
                return float(value)

        parser_map: Dict[PrimitiveType, Callable] = {
            PrimitiveType.STRING: str,
            PrimitiveType.ENUM: str,
            PrimitiveType.BOOLEAN: bool,
            PrimitiveType.NUMBER: number_parser,
            PrimitiveType.UUID: UUID,
            PrimitiveType.DATE_ONLY: date.fromisoformat,
            PrimitiveType.TIME_ONLY: time.fromisoformat,
            PrimitiveType.DATE: datetime.fromisoformat,
            PrimitiveType.POINT: lambda v: (int(v) for v in cast(str, value).split(",")),
            PrimitiveType.BINARY: lambda v: v,  # should not be called
            PrimitiveType.JSON: lambda v: v,
        }

        if schema["column_type"] in parser_map.keys():
            return parser_map[cast(PrimitiveType, schema["column_type"])](value)
        elif isinstance(schema["column_type"], dict) or isinstance(schema["column_type"], list):
            return value
        else:
            ForestLogger.log("error", f"Unknown column type {schema['column_type']}")
            raise AgentToolkitException(f"Unknown column type {schema['column_type']}")

    def _deserialize_relationships(self, name: str, value, collection: Collection):
        ret = {}
        if is_one_to_one(collection.schema):
            return value["data"].get(pk)
        for pk in SchemaUtils.get_primary_keys(collection.schema):
            ret[pk] = value["data"].get(pk)
        return ret
