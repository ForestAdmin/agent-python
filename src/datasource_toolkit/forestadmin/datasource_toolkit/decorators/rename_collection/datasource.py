from typing import Dict, List, Union

from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.rename_collection.collection import RenameCollectionCollectionDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.models.collections import BoundCollection


class RenameCollectionDataSourceDecorator(DatasourceDecorator):
    def __init__(self, child_datasource: Union[Datasource, DatasourceDecorator]):
        self._from_child_name: Dict[str, str] = {}
        self._to_child_name: Dict[str, str] = {}
        super().__init__(child_datasource, RenameCollectionCollectionDecorator)

    @property
    def collections(self) -> List[BoundCollection]:
        return [
            super(RenameCollectionDataSourceDecorator, self).get_collection(collection.name)
            for collection in self.child_datasource.collections
        ]

    def get_collection(self, name: str) -> RenameCollectionCollectionDecorator:
        # Collection has been renamed, user is using the new name
        if name in self._to_child_name.keys():
            return super().get_collection(self._to_child_name[name])

        # Collection has been renamed, user is using the old name
        if name in self._from_child_name.keys():
            raise ForestException(f"Collection '{name}' has been renamed to '{self._from_child_name[name]}'")

        # Collection has not been renamed
        return super().get_collection(name)

    def get_collection_name(self, child_name: str) -> str:
        return self._from_child_name.get(child_name, child_name)

    def rename_collections(self, renames: Dict[str, str]):
        for old_name, new_name in renames.items():
            self.rename_collection(old_name, new_name)

    def rename_collection(self, current_name: str, new_name: str):
        # Check collection exists
        self.get_collection(current_name)

        # Rename collection
        if current_name != new_name:
            # Check new name is not already used
            if any([collection.name == new_name for collection in self.collections]):
                raise ForestException(f"The given new collection name {new_name} is already defined in the dataSource")

            # Check we don't rename a collection twice
            if current_name in self._to_child_name.keys():
                raise ForestException(
                    f"Cannot rename a collection twice: {self._to_child_name[current_name]}->{current_name}->{new_name}"
                )

            self._from_child_name[current_name] = new_name
            self._to_child_name[new_name] = current_name

            for collection in self.collections:
                collection.mark_schema_as_dirty()
