import zoneinfo
from collections import defaultdict
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union, cast

from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyCollection, BaseSqlAlchemyCollectionFactory
from forestadmin.datasource_sqlalchemy.utils.model_converter import CollectionFactory
from forestadmin.datasource_sqlalchemy.utils.query_factory import QueryFactory
from forestadmin.datasource_sqlalchemy.utils.record_serializer import (
    aggregations_to_records,
    instances_to_records,
    projections_to_records,
)
from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships, merge_relationships
from forestadmin.datasource_toolkit.datasources import Datasource, DatasourceException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionResult
from forestadmin.datasource_toolkit.interfaces.fields import (
    FieldType,
    ManyToMany,
    ManyToOne,
    PrimitiveType,
    RelationAlias,
)
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.type_getter import TypeGetter
from sqlalchemy import Table
from sqlalchemy import column as SqlAlchemyColumn
from sqlalchemy.engine import Dialect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapper, RelationshipProperty, sessionmaker


class SqlAlchemyCollectionException(DatasourceException):
    pass


def handle_sqlalchemy_error(fn: Callable[..., Awaitable[Any]]):
    async def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(self, *args, **kwargs)
        except SQLAlchemyError as e:
            raise SqlAlchemyCollectionException(str(e))

    return wrapped


class SqlAlchemyCollectionFactory(BaseSqlAlchemyCollectionFactory):
    def __init__(self, collection: "SqlAlchemyCollection"):
        self._collection = collection

    @property
    def collection(self) -> "SqlAlchemyCollection":
        return self._collection

    def _unknown_fields(self, data: RecordsDataAlias) -> List[str]:
        fields: List[str] = []
        for name in data.keys():
            try:
                self.collection.get_column(name)
            except SqlAlchemyCollectionException:
                fields.append(name)
        return fields

    def init_instance(self, data: RecordsDataAlias) -> "SqlAlchemyCollection":
        if self.collection.model:
            try:
                return self.collection.model(**data)  # type: ignore
            except TypeError as e:
                unknown_fields = self._unknown_fields(data)
                if unknown_fields:
                    raise SqlAlchemyCollectionException(
                        f'Unknow fields "{unknown_fields}" for the model "{self.collection.model.__class__.__name__}"'
                    )
                raise e
        raise


class SqlAlchemyCollection(BaseSqlAlchemyCollection):
    def __init__(
        self,
        name: str,
        datasource: "SqlAlchemyDatasource",
        table: Table,
        mapper: Optional[Mapper] = None,
    ):
        super(SqlAlchemyCollection, self).__init__(name, datasource)
        self._table = table
        self._mapper = mapper
        self._name = name
        self._factory = SqlAlchemyCollectionFactory(self)
        schema = CollectionFactory.build(self.table, self.mapper)
        self.add_fields(schema["fields"])

    @property
    def table(self) -> Table:
        return self._table

    @property
    def mapper(self) -> Optional[Mapper]:
        return self._mapper

    @property
    def model(self) -> Optional[Callable[[Any], Any]]:
        if self.mapper:
            return self.mapper.class_
        return None

    @property
    def factory(self) -> SqlAlchemyCollectionFactory:
        return self._factory

    def get_column(self, name: str) -> SqlAlchemyColumn:
        try:
            return self.mapper.columns[name]  # type: ignore
        except KeyError:
            raise SqlAlchemyCollectionException(f"Unkown field '{name}' for the collection '{self.name}'")

    def _get_relationship(self, name: str) -> RelationshipProperty:
        try:
            return self.mapper.relationships[name]  # type: ignore
        except KeyError:
            raise SqlAlchemyCollectionException(f"Unkown relationship '{name}' for the collection '{self.name}'")

    def get_columns(self, projection: Projection, level: int = 0) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        relationships: Relationships = defaultdict(list)
        columns: List[SqlAlchemyColumn] = [self.get_column(column) for column in projection.columns]
        nested_columns, nested_relationships = self._get_related_column(projection, level)
        columns.extend(nested_columns)
        relationships = merge_relationships(relationships, nested_relationships)
        return columns, relationships

    def _get_related_column(
        self, projection: Projection, level: int = 0
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        relationships: Dict[int, List[SqlAlchemyColumn]] = defaultdict(list)
        columns: List[SqlAlchemyColumn] = []
        for related_field_name, related_projection in projection.relations.items():
            relationships[level].append(self._get_relationship(related_field_name).class_attribute)  # type: ignore
            related_field: RelationAlias = cast(RelationAlias, self.get_field(related_field_name))
            related_collection = self.datasource.get_collection(related_field["foreign_collection"])
            nested_columns, nested_relationships = related_collection.get_columns(related_projection, level + 1)
            columns.extend(nested_columns)
            merge_relationships(relationships, nested_relationships)
        return columns, relationships

    def _normalize_projection(self, projection: Projection):
        # needed to be compliant with the orm result orm
        normalized_projection = projection.columns
        for parent_field, child_fields in projection.relations.items():
            for field in cast(List[str], child_fields):
                normalized_projection.append(f"{parent_field}:{field}")
        return Projection(*normalized_projection)

    async def execute(self, name: str, data: RecordsDataAlias, filter: Optional[Filter]) -> ActionResult:
        return await super().execute(name, data, filter)

    async def aggregate(
        self,
        filter: Optional[Filter],
        aggregation: Aggregation,
        limit: Optional[int] = None,
    ) -> List[AggregateResult]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            dialect: Dialect = session.bind.dialect  #  type: ignore
            filter = cast(Filter, self._cast_filter(filter)) or None
            query = QueryFactory.build_aggregate(dialect, self, filter, aggregation, limit)
            res: List[Dict[str, Any]] = session.execute(query)  #  type: ignore
            return aggregations_to_records(res)

    @handle_sqlalchemy_error
    async def create(self, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            instances = QueryFactory.create(self, data)
            session.bulk_save_objects(instances, return_defaults=True)  # type: ignore
            return instances_to_records(self, instances)

    async def update(self, filter: Optional[Filter], patch: RecordsDataAlias) -> None:
        with self.datasource.Session.begin() as session:  #  type: ignore
            query = QueryFactory.update(self, filter, patch)
            session.execute(query)  # type: ignore

    def _cast_condition_tree(self, tree: ConditionTree) -> ConditionTree:
        if isinstance(tree, ConditionTreeLeaf):
            if TypeGetter.get(tree.value, None) == PrimitiveType.DATE:
                iso_format = tree.value
                if isinstance(iso_format, str):
                    if iso_format[-1] == "Z":
                        iso_format = iso_format[:-1]
                    iso_format = datetime.fromisoformat(iso_format).replace(
                        tzinfo=zoneinfo.ZoneInfo("UTC")
                    )  # type: ignore
                tree = tree.override({"value": iso_format})
        return tree

    def _cast_filter(self, filter: Union[Filter, PaginatedFilter, None]) -> Union[Filter, PaginatedFilter, None]:
        if filter and filter.condition_tree:
            filter = filter.override(
                {"condition_tree": filter.condition_tree.replace(self._cast_condition_tree)}  # type: ignore
            )
        return filter

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            projection = self._normalize_projection(projection)
            filter = cast(PaginatedFilter, self._cast_filter(filter))
            query = QueryFactory.build_list(self, filter, projection)
            res = session.execute(query).all()  #  type: ignore
            records = projections_to_records(projection, res, filter.timezone)  # type: ignore
            return records

    async def delete(self, filter: Optional[Filter]) -> None:
        with self.datasource.Session.begin() as session:  #  type: ignore
            query = QueryFactory.delete(self, filter)
            session.execute(query)  # type: ignore

    async def get_form(
        self, name: str, data: Optional[RecordsDataAlias], filter: Optional[Filter]
    ) -> List[ActionField]:
        return await super().get_form(name, data, filter)


class SqlAlchemyDatasource(Datasource[SqlAlchemyCollection]):
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
