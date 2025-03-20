import json
from enum import Enum
from typing import Any, List, Mapping

from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.fields import is_column
from forestadmin.rpc_common.proto import datasource_pb2, datasource_pb2_grpc, forest_pb2


class DatasourceService(datasource_pb2_grpc.DataSourceServicer):
    def __init__(self, datasource: Datasource):
        self.datasource = datasource
        super().__init__()

    def Schema(self, request, context) -> datasource_pb2.SchemaResponse:
        collections = []
        for collection in self.datasource.collections:
            fields: List[Mapping[str, Any]] = []
            for field_name, field_schema in collection.schema["fields"].items():
                field: Mapping[str, Any] = {**field_schema}

                field["type"] = field["type"].value if isinstance(field["type"], Enum) else field["type"]

                if is_column(field_schema):
                    field["column_type"] = (
                        field["column_type"].value if isinstance(field["column_type"], Enum) else field["column_type"]
                    )
                    field["filter_operators"] = [
                        op.value if isinstance(op, Enum) else op for op in field["filter_operators"]
                    ]
                    field["validations"] = [
                        {
                            **validation,
                            "operator": (
                                validation["operator"].value
                                if isinstance(validation["operator"], Enum)
                                else validation["operator"]
                            ),
                        }
                        for validation in field["validations"]
                    ]
                else:
                    continue
                fields.append({field_name: json.dumps(field).encode("utf-8")})

            try:
                collections.append(
                    forest_pb2.CollectionSchema(
                        name=collection.name,
                        searchable=collection.schema["searchable"],
                        segments=collection.schema["segments"],
                        countable=collection.schema["countable"],
                        charts=collection.schema["charts"],
                        # fields=fields,
                        # actions=actions,
                    )
                )
            except Exception as e:
                print(e)
                raise e
        return datasource_pb2.SchemaResponse(
            Collections=collections,
            Schema=forest_pb2.DataSourceSchema(
                Charts=self.datasource.schema["charts"],
                ConnectionNames=self.datasource.get_native_query_connections(),
            ),
        )
