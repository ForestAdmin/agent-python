from typing import Union

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.ip_white_list_resource import IpWhitelistResource
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, Datasource

DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


class BaseCollectionResource(IpWhitelistResource):
    def __init__(
        self,
        datasource: DatasourceAlias,
        permission: PermissionService,
        ip_white_list_service: IpWhiteListService,
        options: Options,
    ):
        super(BaseCollectionResource, self).__init__(ip_white_list_service, options)
        self.permission = permission
        self.datasource = datasource
