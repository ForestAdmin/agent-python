from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.relaxed_wrappers.collection import RelaxedDatasource
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource


class AgentCustomizationContext:
    def __init__(self, datasource: Datasource[Collection], caller: User):
        self._datasource = datasource
        self._caller = caller

    @property
    def datasource(self) -> RelaxedDatasource:
        return RelaxedDatasource(self._datasource)

    @property
    def caller(self) -> User:
        return self._caller
