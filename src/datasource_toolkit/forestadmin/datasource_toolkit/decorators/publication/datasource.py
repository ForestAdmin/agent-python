from typing import List, Optional, Set, Union

from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.publication.collections import PublicationCollectionDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection


class PublicationDataSourceDecorator(DatasourceDecorator):
    def __init__(self, child_datasource: Union[Datasource, DatasourceDecorator]):
        super().__init__(child_datasource, PublicationCollectionDecorator)
        self._blacklist: Set[str] = set()
        self.child_datasource = child_datasource

    @property
    def collections(self) -> List[BoundCollection]:
        return [self.get_collection(c.name) for c in self.child_datasource.collections if c.name not in self._blacklist]

    def get_collection(self, name: str) -> BoundCollection:
        if name in self._blacklist:
            raise ForestException(f"Collection {name} was removed")

        return super().get_collection(name)

    def keep_collections_matching(self, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None):
        if include is None:
            include = []
        if exclude is None:
            exclude = []
        self._validate_collection_name([*include, *exclude])

        # List collection we're keeping from the white/black list.
        for collection in self.collections:
            if (include and collection.name not in include) or (collection.name in exclude):
                self.remove_collection(collection.name)

    def remove_collection(self, collection_name: str):
        self._validate_collection_name([collection_name])

        # Delete the collection
        self._blacklist.add(collection_name)

        # Tell all collections that their schema is dirty: if we removed a collection, all
        # relations to this collection are now invalid and should be unpublished.
        for collection in self.collections:
            collection.mark_schema_as_dirty()

    def _validate_collection_name(self, names: List[str]):
        for name in names:
            self.get_collection(name)

    def is_published(self, collection_name: str) -> bool:
        return collection_name not in self._blacklist
