import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionFormElement, ActionResult, ActionsScope
from forestadmin.datasource_toolkit.interfaces.chart import Chart
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils
from forestadmin.rpc_common.serializers.actions import (
    ActionFormSerializer,
    ActionFormValuesSerializer,
    ActionResultSerializer,
)
from forestadmin.rpc_common.serializers.collection.aggregation import AggregationSerializer
from forestadmin.rpc_common.serializers.collection.filter import (
    FilterSerializer,
    PaginatedFilterSerializer,
    ProjectionSerializer,
)
from forestadmin.rpc_common.serializers.collection.record import RecordSerializer
from forestadmin.rpc_common.serializers.utils import CallerSerializer

if TYPE_CHECKING:
    from forestadmin.datasource_rpc.datasource import RPCDatasource


class RPCCollection(Collection):
    def __init__(self, name: str, datasource: "RPCDatasource"):
        super().__init__(name, datasource)
        self._rpc_actions = {}
        self._datasource = datasource

    @property
    def datasource(self) -> "RPCDatasource":
        return self._datasource

    def add_rpc_action(self, name: str, action: Dict[str, Any]) -> None:
        if name in self._schema["actions"]:
            raise ValueError(f"Action {name} already exists in collection {self.name}")
        self._schema["actions"][name] = Action(
            scope=ActionsScope(action["scope"]),
            description=action.get("description"),
            submit_button_label=action.get("submit_button_label"),
            generate_file=action.get("generate_file", False),
            static_form=action["static_form"],
        )
        self._rpc_actions[name] = {"form": action["form"]}

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": PaginatedFilterSerializer.serialize(filter_, self),
            "projection": ProjectionSerializer.serialize(projection),
            "collectionName": self.name,
        }
        ret = await self.datasource.requester.list(body=body)
        return [RecordSerializer.deserialize(record, self) for record in ret]

    async def create(self, caller: User, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "data": [RecordSerializer.serialize(r) for r in data],
            "collectionName": self.name,
        }
        response = await self.datasource.requester.create(body)
        return [RecordSerializer.deserialize(record, self) for record in response]

    async def update(self, caller: User, filter_: Optional[Filter], patch: Dict[str, Any]) -> None:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": FilterSerializer.serialize(filter_, self),  # type: ignore
            "patch": RecordSerializer.serialize(patch),
            "collectionName": self.name,
        }
        await self.datasource.requester.update(body)

    async def delete(self, caller: User, filter_: Filter | None) -> None:
        body = json.dumps(
            {
                "caller": CallerSerializer.serialize(caller),
                "filter": FilterSerializer.serialize(filter_, self),  # type: ignore
                "collectionName": self.name,
            }
        )
        await self.datasource.requester.delete(body)

    async def aggregate(
        self, caller: User, filter_: Filter | None, aggregation: Aggregation, limit: int | None = None
    ) -> List[AggregateResult]:
        body = {
            "caller": CallerSerializer.serialize(caller),
            "filter": FilterSerializer.serialize(filter_, self),  # type: ignore
            "aggregation": AggregationSerializer.serialize(aggregation),
            "collectionName": self.name,
        }
        response = await self.datasource.requester.aggregate(body)
        return response

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

        body = {
            "caller": CallerSerializer.serialize(caller) if caller is not None else None,
            "filter": FilterSerializer.serialize(filter_, self) if filter_ is not None else None,
            "data": ActionFormValuesSerializer.serialize(data),  # type: ignore
            "meta": meta,
            "collectionName": self.name,
            "actionName": name,
        }
        response = await self.datasource.requester.get_form(body)
        return ActionFormSerializer.deserialize(response)  # type: ignore

    async def execute(
        self,
        caller: User,
        name: str,
        data: RecordsDataAlias,
        filter_: Optional[Filter],
    ) -> ActionResult:
        if name not in self._schema["actions"]:
            raise ValueError(f"Action {name} does not exist in collection {self.name}")

        body = {
            "caller": CallerSerializer.serialize(caller) if caller is not None else None,
            "filter": FilterSerializer.serialize(filter_, self) if filter_ is not None else None,
            "data": ActionFormValuesSerializer.serialize(data),
            "collectionName": self.name,
            "actionName": name,
        }
        response = await self.datasource.requester.execute(body)
        return ActionResultSerializer.deserialize(response)

    async def render_chart(self, caller: User, name: str, record_id: List) -> Chart:
        if name not in self._schema["charts"].keys():
            raise ValueError(f"Chart {name} does not exist in collection {self.name}")

        ret = []
        for i, value in enumerate(record_id):
            pk_field = SchemaUtils.get_primary_keys(self.schema)[i]
            type_record_id = self.schema["fields"][pk_field]["column_type"]  # type: ignore

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

        body = {
            "caller": CallerSerializer.serialize(caller) if caller is not None else None,
            "name": name,
            "collectionName": self.name,
            "recordId": ret,
        }
        return await self.datasource.requester.collection_render_chart(body)

    def get_native_driver(self):
        ForestLogger.log(
            "error",
            "Get_native_driver is not available on RPCCollection. "
            "Please use execute_native_query on the rpc datasource instead",
        )
        pass
