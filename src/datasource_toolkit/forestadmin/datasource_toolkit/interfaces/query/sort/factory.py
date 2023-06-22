from typing import Union

from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SortFactory:
    @staticmethod
    def by_primary_keys(collection: Union[CollectionCustomizer, Collection]) -> Sort:
        return Sort([{"field": pk, "ascending": True} for pk in SchemaUtils.get_primary_keys(collection.schema)])
