from typing import Callable, Type

from forestadmin.datasource_toolkit.decorators.collections import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.models.collections import Datasource


class DatasourceDecorator(Datasource[CollectionDecorator]):
    def __init__(self, child_datasource: Datasource[Collection], collection_decorator_ctor: Type[CollectionDecorator]):

        setattr(child_datasource, "add_collection", self._add_collection_decorator(child_datasource.add_collection))
        self._collection_decorator_ctor = collection_decorator_ctor
        self.child_datasource = child_datasource

        for collection in self.child_datasource.collections:
            self.add_collection(self._collection_decorator_ctor(collection, self))

    def _add_collection_decorator(self, child_datasource_add_collection: Callable[[Collection], None]):
        def decorated(collection: Collection):
            child_datasource_add_collection(collection)
            self.add_collection(self._collection_decorator_ctor(collection, self))

        return decorated
