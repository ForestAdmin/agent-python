import sys
from typing import Optional

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.context.relaxed_wrappers.collection import RelaxedDatasource
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource


class AgentCustomizationContext:
    def __init__(self, datasource: Datasource[Collection], timezone: Optional[zoneinfo.ZoneInfo] = None):
        self._datasource = datasource
        self.timezone = timezone

    @property
    def datasource(self) -> RelaxedDatasource:
        return RelaxedDatasource(self._datasource)
