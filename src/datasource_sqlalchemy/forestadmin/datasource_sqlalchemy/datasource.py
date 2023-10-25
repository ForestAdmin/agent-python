from typing import Any, Dict, Optional

from forestadmin.datasource_sqlalchemy.collections import SqlAlchemyCollection
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyDatasourceException
from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyDatasource
from sqlalchemy import create_engine
from sqlalchemy.orm import Mapper, sessionmaker


class SqlAlchemyDatasource(BaseSqlAlchemyDatasource):
    def __init__(self, Base: Any, db_uri: Optional[str] = None) -> None:
        super().__init__()
        self._base = Base
        self.__is_using_flask_sqlalchemy = hasattr(Base, "Model")

        bind = create_engine(db_uri, echo=False) if db_uri is not None else self._find_db_uri(Base)
        if bind is None:
            raise SqlAlchemyDatasourceException(
                "Cannot find database uri in your SQLAlchemy Base class. "
                + "You can pass it as a param: SqlAlchemyDatasource(..., db_uri='sqlite:///path/to/db.sql')."
            )

        if self.__is_using_flask_sqlalchemy:
            self._base = self._base.Model

        self.Session = sessionmaker(bind)
        self._create_collections()

    def _find_db_uri(self, base_class):
        engine = None
        try:
            if self.__is_using_flask_sqlalchemy:
                engine = base_class.engine
            else:
                engine = base_class.metadata.bind.engine
            return engine
        except Exception:
            return None

    def _create_collections(self):
        mappers = self.build_mappers()
        for table in self._base.metadata.sorted_tables:
            if table.name not in mappers:
                class_ = type(f"SQLAlchemyImpTable_{table.name}", (), {})
                self._base.registry.map_imperatively(class_, table)
                mappers = self.build_mappers()

        for table in self._base.metadata.sorted_tables:
            if table.name in mappers:
                collection = SqlAlchemyCollection(table.name, self, table, mappers[table.name])
                self.add_collection(collection)

    def build_mappers(self) -> Dict[str, Mapper]:
        mappers: Dict[str, Mapper] = {}
        for mapper in self._base.registry.mappers:
            mappers[mapper.persist_selectable.name] = mapper
        return mappers

    # unused code, can be use full but can be remove
    # from forestadmin.datasource_toolkit.datasources import DatasourceException
    # from forestadmin.datasource_toolkit.interfaces.fields import FieldType, ManyToMany, ManyToOne
    # def _create_secondary_collection(self, table: Any):
    #     try:
    #         collection = self.get_collection(table.name)
    #     except DatasourceException:
    #         Secondary = type(str(table.name), tuple(), {})  # type: ignore
    #         mapper = self._base.registry.map_imperatively(Secondary, table)
    #         collection = SqlAlchemyCollection(table.name, self, table, mapper)
    #         self.add_collection(collection)
    #     return collection

    # def _create_secondary_relation(
    #     self,
    #     collection: SqlAlchemyCollection,
    #     related_collection_name: str,
    #     many_to_many: ManyToMany,
    # ):
    #     collection.add_field(
    #         related_collection_name.lower(),
    #         ManyToOne(
    #             foreign_collection=related_collection_name,
    #             foreign_key=many_to_many["origin_key"],
    #             foreign_key_target=many_to_many["origin_key_target"],
    #             type=FieldType.MANY_TO_ONE,
    #         ),
    #     )
    #     return many_to_many["foreign_collection"].lower()
