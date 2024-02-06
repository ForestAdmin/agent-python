import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_sqlalchemy.exceptions import SqlAlchemyCollectionException, handle_sqlalchemy_error
from forestadmin.datasource_sqlalchemy.interfaces import (
    BaseSqlAlchemyCollection,
    BaseSqlAlchemyCollectionFactory,
    BaseSqlAlchemyDatasource,
)
from forestadmin.datasource_sqlalchemy.utils.model_converter import CollectionFactory
from forestadmin.datasource_sqlalchemy.utils.query_factory import QueryFactory
from forestadmin.datasource_sqlalchemy.utils.record_serializer import (
    aggregations_to_records,
    instances_to_records,
    projections_to_records,
)
from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships, merge_relationships
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType, RelationAlias
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
from sqlalchemy.orm import Mapper, RelationshipProperty
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import Alias, alias


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
                        f'Unknown fields "{unknown_fields}" for the model "{self.collection.model.__class__.__name__}"'
                    )
                raise e
        raise


class SqlAlchemyCollection(BaseSqlAlchemyCollection):
    def __init__(
        self,
        name: str,
        datasource: BaseSqlAlchemyDatasource,
        table: Table,
        mapper: Optional[Mapper] = None,
    ):
        super(SqlAlchemyCollection, self).__init__(name, datasource)
        self._table = table
        self._mapper = mapper
        self._name = name
        self._factory = SqlAlchemyCollectionFactory(self)
        self._aliases: Dict[str, Alias] = {}
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

    def get_native_driver(self) -> Session:
        return self.datasource.Session

    def get_column(self, name: str, alias_: Optional[Alias] = None) -> SqlAlchemyColumn:
        mapper = self.mapper
        if alias_ is not None:
            mapper = alias_
        try:
            if hasattr(mapper, "synonyms") and name in mapper.synonyms:
                return mapper.columns[mapper.synonyms[name].name]
            return mapper.columns[name]  # type: ignore
        except KeyError:
            raise SqlAlchemyCollectionException(f"Unknown field '{name}' for the collection '{self.name}'")

    def _get_relationship(self, name: str) -> RelationshipProperty:
        try:
            return self.mapper.relationships[name]  # type: ignore
        except KeyError:
            raise SqlAlchemyCollectionException(f"Unknown relationship '{name}' for the collection '{self.name}'")

    def get_columns(
        self, projection: Projection, level: int = 0, alias_: Optional[Alias] = None
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        relationships: Relationships = defaultdict(list)
        columns: List[SqlAlchemyColumn] = [self.get_column(column, alias_) for column in projection.columns]
        nested_columns, nested_relationships = self._get_related_column(projection, level)
        columns.extend(nested_columns)
        relationships = merge_relationships(relationships, nested_relationships)
        return columns, relationships

    def _get_alias(self, mapper: Mapper, name: str):
        alias_name = f"alias_{name}"
        if alias_name not in self._aliases:
            self._aliases[alias_name] = alias(mapper, alias_name)
        return self._aliases[alias_name]

    def _get_related_column(
        self, projection: Projection, level: int = 0
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        relationships: Dict[int, List[SqlAlchemyColumn]] = defaultdict(list)
        columns: List[SqlAlchemyColumn] = []
        for related_field_name, related_projection in projection.relations.items():
            related_field: RelationAlias = cast(RelationAlias, self.get_field(related_field_name))
            related_collection = self.datasource.get_collection(related_field["foreign_collection"])
            alias_: Alias = self._get_alias(related_collection.mapper, related_field_name)  # type: ignore
            nested_columns, nested_relationships = related_collection.get_columns(related_projection, level + 1, alias_)
            columns.extend(nested_columns)

            relationship = self._get_relationship(related_field_name)
            relationships[level].append((alias_, relationship.class_attribute))  # type: ignore

            merge_relationships(relationships, nested_relationships)
        return columns, relationships

    def _normalize_projection(self, projection: Projection, prefix: str = "") -> Projection:
        # needed to be compliant with the orm result orm
        normalized_projection = [f"{prefix}{col}" for col in projection.columns]
        for parent_field, child_fields in projection.relations.items():
            normalized_projection.extend(self._normalize_projection(child_fields, f"{prefix}{parent_field}:"))
        return Projection(*normalized_projection)

    async def aggregate(
        self,
        caller: User,
        filter_: Optional[Filter],
        aggregation: Aggregation,
        limit: Optional[int] = None,
    ) -> List[AggregateResult]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            dialect: Dialect = session.bind.dialect  #  type: ignore
            filter_ = cast(Filter, self._cast_filter(filter_)) or None
            query = QueryFactory.build_aggregate(dialect, self, filter_, aggregation, limit)
            res: List[Dict[str, Any]] = session.execute(query)  #  type: ignore
            return aggregations_to_records(res)

    @handle_sqlalchemy_error
    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            instances = QueryFactory.create(self, data)
            session.bulk_save_objects(instances, return_defaults=True)  # type: ignore
            return instances_to_records(self, instances)

    async def update(self, caller: User, filter_: Optional[Filter], patch: RecordsDataAlias) -> None:
        with self.datasource.Session.begin() as session:  #  type: ignore
            query = QueryFactory.update(self, filter_, patch)
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

    def _cast_filter(self, filter_: Union[Filter, PaginatedFilter, None]) -> Union[Filter, PaginatedFilter, None]:
        if filter_ and filter_.condition_tree:
            filter_ = filter_.override(
                {"condition_tree": filter_.condition_tree.replace(self._cast_condition_tree)}  # type: ignore
            )
        return filter_

    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        with self.datasource.Session.begin() as session:  #  type: ignore
            normalized_projection = self._normalize_projection(projection)
            filter_ = cast(PaginatedFilter, self._cast_filter(filter_))
            query = QueryFactory.build_list(self, filter_, normalized_projection)
            res = session.execute(query).all()  #  type: ignore
            records = projections_to_records(normalized_projection, res, filter_.timezone)  # type: ignore
            return records

    async def delete(self, caller: User, filter_: Optional[Filter]) -> None:
        with self.datasource.Session.begin() as session:  #  type: ignore
            query = QueryFactory.delete(self, filter_)
            session.execute(query)  # type: ignore
