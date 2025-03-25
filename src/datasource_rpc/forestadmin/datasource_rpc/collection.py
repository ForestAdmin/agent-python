import json
from typing import Any, Dict, List, Optional

import urllib3
from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionFormElement, ActionResult, ActionsScope
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.rpc_common.hmac import generate_hmac
from forestadmin.rpc_common.serializers.actions import ActionFormSerializer, ActionResultSerializer
from forestadmin.rpc_common.serializers.aes import aes_decrypt, aes_encrypt
from forestadmin.rpc_common.serializers.collection.aggregation import AggregationSerializer
from forestadmin.rpc_common.serializers.collection.filter import (
    FilterSerializer,
    PaginatedFilterSerializer,
    ProjectionSerializer,
)
from forestadmin.rpc_common.serializers.collection.record import RecordSerializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer


class RPCCollection(Collection):
    def __init__(self, name: str, datasource: Datasource, connection_uri: str, secret_key: str):
        super().__init__(name, datasource)
        self.connection_uri = connection_uri
        self.secret_key = secret_key
        self.aes_key = secret_key[:16].encode()
        self.aes_iv = secret_key[-16:].encode()
        self.http = urllib3.PoolManager()
        self._rpc_actions = {}

    def add_rpc_action(self, name: str, action: Dict[str, Any]) -> None:
        if name in self._schema["actions"]:
            raise ValueError(f"Action {name} already exists in collection {self.name}")
        self._schema["actions"][name] = Action(
            scope=ActionsScope(action["scope"]),
            description=action.get("description"),
            submit_button_label=action.get("submit_button_label"),
            generate_file=action.get("generate_file", False),
            # form=action.get("form"),
            static_form=action["static_form"],
        )
        self._rpc_actions[name] = {"form": action["form"]}

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "filter": PaginatedFilterSerializer.serialize(filter_, self),
                "projection": ProjectionSerializer.serialize(projection),
                "collectionName": self.name,
            }
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/list",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)

        return [RecordSerializer.deserialize(record, self) for record in json.loads(ret)]

    async def create(self, caller: User, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "data": [RecordSerializer.serialize(r) for r in data],
                "collectionName": self.name,
            }
        )
        body = aes_encrypt(body, self.aes_key, self.aes_iv)
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/create",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        return [RecordSerializer.deserialize(record, self) for record in json.loads(response.data.decode("utf-8"))]

    async def update(self, caller: User, filter_: Optional[Filter], patch: Dict[str, Any]) -> None:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "filter": FilterSerializer.serialize(filter_, self),
                "patch": RecordSerializer.serialize(patch),
                "collectionName": self.name,
            }
        )
        body = aes_encrypt(body, self.aes_key, self.aes_iv)
        self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/update",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )

    async def delete(self, caller: User, filter_: Filter | None) -> None:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "filter": FilterSerializer.serialize(filter_, self),
                "collectionName": self.name,
            }
        )
        self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/delete",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )

    async def aggregate(
        self, caller: User, filter_: Filter | None, aggregation: Aggregation, limit: int | None = None
    ) -> List[AggregateResult]:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "filter": FilterSerializer.serialize(filter_, self),
                "aggregation": AggregationSerializer.serialize(aggregation),
                "collectionName": self.name,
            }
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/aggregate",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        return json.loads(ret)

    async def get_form(
        self,
        caller: User,
        name: str,
        data: Optional[RecordsDataAlias] = None,
        filter_: Optional[Filter] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> List[ActionFormElement]:
        if name not in self._schema["actions"]:
            raise ValueError(f"Action {name} does not exist in collection {self.name}")

        if self._schema["actions"][name].static_form:
            return self._rpc_actions[name]["form"]

        body = aes_encrypt(
            json.dumps(
                {
                    "caller": CallerSerializer.serialize(caller) if caller is not None else None,
                    "filter": FilterSerializer.serialize(filter_, self) if filter_ is not None else None,
                    "data": data,
                    "meta": meta,
                    "collectionName": self.name,
                    "actionName": name,
                }
            ),
            self.aes_key,
            self.aes_iv,
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/get-form",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        ret = ActionFormSerializer.deserialize(json.loads(ret))
        return ret

    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        filter_: Optional[Filter],
    ) -> ActionResult:
        if name not in self._schema["actions"]:
            raise ValueError(f"Action {name} does not exist in collection {self.name}")

        body = aes_encrypt(
            json.dumps(
                {
                    "caller": CallerSerializer.serialize(caller) if caller is not None else None,
                    "filter": FilterSerializer.serialize(filter_, self) if filter_ is not None else None,
                    "data": data,
                    "collectionName": self.name,
                    "actionName": name,
                }
            ),
            self.aes_key,
            self.aes_iv,
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/execute",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        ret = json.loads(ret)
        ret = ActionResultSerializer.deserialize(ret)
        return ret

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        if name not in self._schema["charts"].keys():
            raise ValueError(f"Chart {name} does not exist in collection {self.name}")

        ret = []
        for i, value in enumerate(record_id):
            type_record_id = self.schema["fields"][SchemaUtils.get_primary_keys(self.schema)[i]]["column_type"]

            if type_record_id == PrimitiveType.DATE:
                ret.append(value.isoformat())
            elif type_record_id == PrimitiveType.DATE_ONLY:
                ret.append(value.isoformat())
            elif type_record_id == PrimitiveType.DATE:
                ret.append(value.isoformat())
            elif type_record_id == PrimitiveType.POINT:
                ret.append((value[0], value[1]))
            elif type_record_id == PrimitiveType.UUID:
                ret.append(str(value))
            else:
                ret.append(value)

        body = aes_encrypt(
            json.dumps(
                {
                    "caller": CallerSerializer.serialize(caller) if caller is not None else None,
                    "name": name,
                    "collectionName": self.name,
                    "recordId": ret,
                }
            ),
            self.aes_key,
            self.aes_iv,
        )
        response = self.http.request(
            "POST",
            f"http://{self.connection_uri}/collection/render-chart",
            body=body,
            headers={"X-FOREST-HMAC": generate_hmac(self.secret_key.encode("utf-8"), body.encode("utf-8"))},
        )
        ret = aes_decrypt(response.data.decode("utf-8"), self.aes_key, self.aes_iv)
        ret = json.loads(ret)
        return ret

    def get_native_driver(self):
        ForestLogger.log(
            "error",
            "Get_native_driver is not available on RPCCollection. "
            "Please use execute_native_query on the rpc datasource instead",
        )
        pass
