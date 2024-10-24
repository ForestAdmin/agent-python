from typing import Any, Dict, Literal, Union

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.collections.decorators import authenticate, check_method, ip_white_list
from forestadmin.agent_toolkit.resources.ip_white_list_resource import IpWhitelistResource
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.utils.context import HttpResponseBuilder, Request, RequestMethod, Response
from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.exceptions import BusinessError
from forestadmin.datasource_toolkit.interfaces.fields import Column, is_column
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, Datasource

LiteralMethod = Literal["capabilities"]
DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


class CapabilitiesResource(IpWhitelistResource):
    def __init__(
        self,
        datasource: DatasourceAlias,
        ip_white_list_service: IpWhiteListService,
        options: Options,
    ):
        super().__init__(ip_white_list_service, options)
        self.datasource = datasource

    @ip_white_list
    async def dispatch(self, request: Request, method_name: LiteralMethod) -> Response:
        method = getattr(self, method_name)
        try:
            return await method(request)
        except BusinessError as e:
            return HttpResponseBuilder.build_client_error_response([e])
        except Exception as e:
            ForestLogger.log("exception", e)
            return HttpResponseBuilder.build_client_error_response([e])

    @check_method(RequestMethod.POST)
    @authenticate
    async def capabilities(self, request: Request) -> Response:
        ret = {"collections": []}
        requested_collections = request.body.get("collectionNames", [])
        for collection_name in requested_collections:
            ret["collections"].append(self._get_collection_capability(collection_name))
        return HttpResponseBuilder.build_success_response(ret)

    def _get_collection_capability(self, collection_name: str) -> Dict[str, Any]:
        collection = self.datasource.get_collection(collection_name)
        fields = []
        for field_name, field_schema in collection.schema["fields"].items():
            if is_column(field_schema):
                fields.append(self._get_field_capabilities(field_name, field_schema))
        return {
            "name": collection_name,
            "fields": fields,
        }

    def _get_field_capabilities(self, field_name: str, field_schema: Column) -> Dict[str, Any]:
        return {
            "name": field_name,
            "type": SchemaFieldGenerator.build_column_type(field_schema["column_type"]),
            "operators": sorted([op.value for op in field_schema["filter_operators"]]),
        }
