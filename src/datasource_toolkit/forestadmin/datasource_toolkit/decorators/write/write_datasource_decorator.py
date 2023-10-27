from typing import Union

from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.write.create_relations.create_relations_collection import (
    CreateRelationsCollection,
)
from forestadmin.datasource_toolkit.decorators.write.update_relations.update_relations_collection import (
    UpdateRelationsCollection,
)
from forestadmin.datasource_toolkit.decorators.write.write_replace.write_replace_collection import (
    WriteReplaceCollection,
)


class WriteDataSourceDecorator(DatasourceDecorator):
    def __init__(self, child_datasource: Union[Datasource, DatasourceDecorator]) -> None:
        self._create: DatasourceDecorator = DatasourceDecorator(child_datasource, CreateRelationsCollection)
        self._update: DatasourceDecorator = DatasourceDecorator(self._create, UpdateRelationsCollection)
        super().__init__(self._update, WriteReplaceCollection)
