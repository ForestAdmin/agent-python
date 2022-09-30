from typing import Any

from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection


class CustomizedDatasource(Datasource[CustomizedCollection]):  # type: ignore
    def __init__(self, child_datasource: Datasource[BoundCollection]):
        super().__init__()
        self.child_datasource = child_datasource

    def __getattr__(self, __name: str) -> Any:
        return getattr(self.child_datasource, __name)
