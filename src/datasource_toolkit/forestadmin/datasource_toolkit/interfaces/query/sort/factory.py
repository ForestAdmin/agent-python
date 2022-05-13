from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SortFactory:
    @staticmethod
    def by_primary_keys(collection: Collection) -> Sort:
        return Sort(*[{"field": pk, "ascending": True} for pk in SchemaUtils.get_primary_keys(collection.schema)])
