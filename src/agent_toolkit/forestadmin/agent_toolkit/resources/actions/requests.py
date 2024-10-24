from typing import Any, Dict, Optional, Union

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.resources.collections.requests import RequestArgs as CollectionRequestArgs
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod, User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection
from typing_extensions import Self


class RequestActionException(AgentToolkitException):
    pass


class RequestArgs(CollectionRequestArgs):
    action_name: str


class ActionRequest(RequestCollection):
    def __init__(
        self,
        method: RequestMethod,
        action_name: str,
        collection: Union[Collection, CollectionCustomizer],
        headers: Dict[str, str],
        client_ip: str,
        query: Dict[str, str],
        user: Optional[User] = None,
        body: Optional[Dict[str, Any]] = None,
    ):
        super(ActionRequest, self).__init__(
            method=method,
            collection=collection,
            headers=headers,
            client_ip=client_ip,
            query=query,
            user=user,
            body=body,
        )
        self.action_name = action_name

    @staticmethod
    def from_request_args(
        request: Request, datasource: Union[Datasource[BoundCollection], DatasourceCustomizer]
    ) -> RequestArgs:
        request_args = RequestCollection.from_request_args(request, datasource)
        try:
            action_name: int = request.query["action_name"]  # type: ignore
        except KeyError:
            raise RequestActionException("'action_name' is missing in the request")
        name = list(request_args["collection"].schema["actions"].keys())[action_name]
        return {**request_args, "action_name": name}

    @classmethod
    def from_request(
        cls, request: Request, datasource: Union[Datasource[BoundCollection], DatasourceCustomizer]
    ) -> Self:
        return cls(**cls.from_request_args(request, datasource))
