import json
from typing import Any, Dict, List, Optional

import urllib3
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.rpc_common.serializers.collection.aggregation import AggregationSerializer
from forestadmin.rpc_common.serializers.collection.filter import (
    FilterSerializer,
    PaginatedFilterSerializer,
    ProjectionSerializer,
)
from forestadmin.rpc_common.serializers.collection.record import RecordSerializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer


class RPCCollection(Collection):
    def __init__(self, name: str, datasource: Datasource, connection_uri: str):
        super().__init__(name, datasource)
        self.connection_uri = connection_uri
        self.http = urllib3.PoolManager()

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": PaginatedFilterSerializer.serialize(filter_, self),
            "projection": ProjectionSerializer.serialize(projection),
            "collectionName": self.name,
        }
        response = self.http.request("POST", f"http://{self.connection_uri}/collection/list", body=json.dumps(body))
        return [RecordSerializer.deserialize(record, self) for record in json.loads(response.data.decode("utf-8"))]

    async def create(self, caller: User, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "data": [RecordSerializer.serialize(r) for r in data],
            "collectionName": self.name,
        }
        response = self.http.request("POST", f"http://{self.connection_uri}/collection/create", body=json.dumps(body))
        return [RecordSerializer.deserialize(record, self) for record in json.loads(response.data.decode("utf-8"))]

    async def update(self, caller: User, filter_: Optional[Filter], patch: Dict[str, Any]) -> None:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": FilterSerializer.serialize(filter_, self),
            "patch": RecordSerializer.serialize(patch),
            "collectionName": self.name,
        }
        self.http.request("POST", f"http://{self.connection_uri}/collection/update", body=json.dumps(body))

    async def delete(self, caller: User, filter_: Filter | None) -> None:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": FilterSerializer.serialize(filter_, self),
            "collectionName": self.name,
        }
        self.http.request("POST", f"http://{self.connection_uri}/collection/delete", body=json.dumps(body))

    async def aggregate(
        self, caller: User, filter_: Filter | None, aggregation: Aggregation, limit: int | None = None
    ) -> List[AggregateResult]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": FilterSerializer.serialize(filter_, self),
            "aggregation": AggregationSerializer.serialize(aggregation),
            "collectionName": self.name,
        }
        response = self.http.request(
            "POST", f"http://{self.connection_uri}/collection/aggregate", body=json.dumps(body)
        )
        return json.loads(response.data.decode("utf-8"))
