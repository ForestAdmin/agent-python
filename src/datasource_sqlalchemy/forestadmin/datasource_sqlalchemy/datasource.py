from typing import Any, Dict

from forestadmin.datasource_sqlalchemy.collections import SqlAlchemyCollection
from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyDatasource
from forestadmin.datasource_toolkit.datasources import DatasourceException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, ManyToMany, ManyToOne
from sqlalchemy.orm import Mapper, sessionmaker


class SqlAlchemyDatasource(BaseSqlAlchemyDatasource):
    def __init__(self, Base: Any) -> None:
        super().__init__()
        self._base = Base
        self.Session = sessionmaker(self._base.metadata.bind)  # type: ignore
        self._create_collections()

    def build_mappers(self) -> Dict[str, Mapper]:
        mappers: Dict[str, Mapper] = {}
        for mapper in self._base.registry.mappers:
            mappers[mapper.persist_selectable.name] = mapper
        return mappers

    def _create_secondary_collection(self, table: Any):
        try:
            collection = self.get_collection(table.name)
        except DatasourceException:
            Secondary = type(str(table.name), tuple(), {})  # type: ignore
            mapper = self._base.registry.map_imperatively(Secondary, table)
            collection = SqlAlchemyCollection(table.name, self, table, mapper)
            self.add_collection(collection)
        return collection

    def _create_secondary_relation(
        self,
        collection: SqlAlchemyCollection,
        related_collection_name: str,
        many_to_many: ManyToMany,
    ):
        collection.add_field(
            related_collection_name.lower(),
            ManyToOne(
                foreign_collection=related_collection_name,
                foreign_key=many_to_many["origin_key"],
                foreign_key_target=many_to_many["origin_key_target"],
                type=FieldType.MANY_TO_ONE,
            ),
        )
        return many_to_many["foreign_collection"].lower()

    def _create_collections(self):
        mappers = self.build_mappers()
        for table in self._base.metadata.sorted_tables:
            if table.name in mappers:
                collection = SqlAlchemyCollection(table.name, self, table, mappers[table.name])
                self.add_collection(collection)
