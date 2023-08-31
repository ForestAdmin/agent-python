from typing import Union

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.services.permissions.permission_service import PermissionService
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection, Datasource

DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


class BaseCollectionResource(BaseResource):
    def __init__(self, datasource: DatasourceAlias, permission: PermissionService, options: Options):  # noqa: F821
        super(BaseCollectionResource, self).__init__(options)
        self.permission = permission
        self.datasource = datasource
