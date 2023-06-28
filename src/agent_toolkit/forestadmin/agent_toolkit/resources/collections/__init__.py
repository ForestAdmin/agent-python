from typing import TypeVar, Union

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.services.permissions import PermissionService
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.datasource_customizer import DatasourceCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource

BoundCollection = TypeVar("BoundCollection", bound=Collection)

DatasourceAlias = Union[Datasource[BoundCollection], DatasourceCustomizer]


class BaseCollectionResource(BaseResource):
    def __init__(self, datasource: DatasourceAlias[BoundCollection], permission: PermissionService, options: Options):
        super(BaseCollectionResource, self).__init__(options)
        self.permission = permission
        self.datasource = datasource
