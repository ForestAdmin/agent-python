from typing import Dict

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    Collection as CollectionInterface,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import (
    Datasource as DatasourceInterface,
)


class DatasourceException(DatasourceToolkitException):
    pass


class Datasource(DatasourceInterface):
    def __init__(self) -> None:
        self._collections: Dict[str, CollectionInterface]

    @property
    def collections(self) -> Dict[str, CollectionInterface]:
        return self._collections

    def get_collection(self, name: str) -> CollectionInterface:
        try:
            collection: CollectionInterface = self._collections[name]
        except KeyError:
            raise DatasourceException(f"Collection '{name}' not found")
        else:
            return collection

    def add_collection(self, collection: CollectionInterface) -> None:
        if collection.name in self._collections:
            raise DatasourceException(f"Collection '{collection.name}' already defined in datasource")
        self._collections[collection.name] = collection
