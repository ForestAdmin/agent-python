from typing import Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.chart import Chart


class DatasourceDecorator(Datasource):
    def __init__(
        self, child_datasource: Union[Datasource, "DatasourceDecorator"], class_collection_decorator: type
    ) -> None:
        super().__init__()
        self.child_datasource = child_datasource
        self.class_collection_decorator = class_collection_decorator

        for collection in self.child_datasource.collections:
            self.add_collection(self.class_collection_decorator(collection, self))

    def get_charts(self):
        return self.child_datasource.get_charts()

    async def render_chart(self, caller: User, name: str) -> Chart:
        return await self.child_datasource.render_chart(caller, name)
