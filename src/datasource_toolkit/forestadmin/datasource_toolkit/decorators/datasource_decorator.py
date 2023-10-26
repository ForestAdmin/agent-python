from typing import Dict, Union

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.chart import Chart


class DatasourceDecorator(Datasource):
    def __init__(
        self, child_datasource: Union[Datasource, "DatasourceDecorator"], class_collection_decorator: type
    ) -> None:
        super().__init__()
        self.child_datasource = child_datasource
        self.class_collection_decorator = class_collection_decorator
        self._decorators: Dict[Collection, CollectionDecorator] = {}

        for collection in self.child_datasource.collections:
            self.add_collection(self.class_collection_decorator(collection, self))

    @property
    def schema(self):
        return self.child_datasource.schema

    @property
    def collections(self):
        return [self.get_collection(c.name) for c in self.child_datasource.collections]

    def get_collection(self, name: str) -> CollectionDecorator:
        collection = self.child_datasource.get_collection(name)
        if collection not in self._decorators:
            self._decorators[collection] = self.class_collection_decorator(collection, self)
        return self._decorators.get(collection)

    def get_charts(self):
        return self.child_datasource.get_charts()

    async def render_chart(self, caller: User, name: str) -> Chart:
        return await self.child_datasource.render_chart(caller, name)
