from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast

from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyCollection
from forestadmin.datasource_sqlalchemy.utils.aggregation import AggregationFactory
from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships, merge_relationships
from forestadmin.datasource_sqlalchemy.utils.type_converter import FilterOperator
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from sqlalchemy import and_
from sqlalchemy import column as SqlAlchemyColumn
from sqlalchemy import delete, or_, select, update
from sqlalchemy.engine import Dialect
from sqlalchemy.sql.elements import BooleanClauseList, UnaryExpression


class ConditionTreeFactoryException(DatasourceToolkitException):
    pass


class ConditionTreeFactory:
    AGGREGATORS = {Aggregator.AND: and_, Aggregator.OR: or_}

    @classmethod
    def _build_leaf_condition(cls, collection: BaseSqlAlchemyCollection, leaf: ConditionTreeLeaf) -> Tuple[Any, Any]:
        projection = leaf.projection
        columns, relationships = collection.get_columns(projection)
        operator = FilterOperator.get_operator(columns, leaf.operator)
        return operator(leaf.value), relationships

    @classmethod
    def _get_aggregator(cls, aggregator: Aggregator):
        try:
            return cls.AGGREGATORS[aggregator]
        except KeyError:
            raise DatasourceToolkitException(f"Unable to handle the aggregator {aggregator}")

    @classmethod
    def _build_branch_condition(
        cls, collection: BaseSqlAlchemyCollection, branch: ConditionTreeBranch
    ) -> Tuple[Any, Any]:
        relationships: Dict[int, List[SqlAlchemyColumn]] = defaultdict(list)
        aggregator = cls._get_aggregator(branch.aggregator)
        clauses: List[Any] = []
        for condition in branch.conditions:
            clause, leaf_relationships = cls._build(collection, condition)
            clauses.append(clause)
            relationships = merge_relationships(relationships, leaf_relationships)
        return aggregator(*clauses), relationships

    @classmethod
    def _build(cls, collection: BaseSqlAlchemyCollection, condition_tree: ConditionTree):
        if isinstance(condition_tree, ConditionTreeLeaf):
            return cls._build_leaf_condition(collection, condition_tree)
        elif isinstance(condition_tree, ConditionTreeBranch):
            return cls._build_branch_condition(collection, condition_tree)
        raise ConditionTreeFactoryException(f"Unable to handle the type {condition_tree.__class__}")

    @classmethod
    def build(cls, collection: BaseSqlAlchemyCollection, condition_tree: ConditionTree):
        return cls._build(collection, condition_tree)


class FilterOptions(TypedDict):
    clauses: Optional[BooleanClauseList]
    relationships: Relationships


class PaginatedFilterOptions(FilterOptions):
    order_by: Optional[List[UnaryExpression]]


class FilterFactory:
    @classmethod
    def build(cls, collection: BaseSqlAlchemyCollection, filter: Optional[Filter]) -> FilterOptions:
        res: FilterOptions = {
            "relationships": defaultdict(list),
            "clauses": None,
        }
        if filter and filter.condition_tree:
            res["clauses"], clauses_relationships = ConditionTreeFactory.build(collection, filter.condition_tree)
            res["relationships"] = merge_relationships(res["relationships"], clauses_relationships)
        return res


class PaginatedFilterFactory:
    @staticmethod
    def get_order_by(collection: BaseSqlAlchemyCollection, filter: PaginatedFilter) -> Tuple[List[Any], Relationships]:
        relationships: Relationships = defaultdict(list)
        order_clauses: List[Any] = []
        for sort in cast(List[PlainSortClause], filter.sort or []):
            field = sort["field"]
            if "." in field:
                field = field.replace(".", ":")
            columns, nested_relationships = collection.get_columns(Projection(field))
            relationships = merge_relationships(relationships, nested_relationships)
            if sort["ascending"]:
                order_clauses.append(columns[0].asc())  # type: ignore
            else:
                order_clauses.append(columns[0].desc())  # type: ignore
        return order_clauses, relationships

    @classmethod
    def build(cls, collection: BaseSqlAlchemyCollection, filter: PaginatedFilter) -> PaginatedFilterOptions:
        filter_ = FilterFactory.build(collection, filter.to_base_filter())
        res: PaginatedFilterOptions = {
            "relationships": filter_["relationships"],
            "clauses": filter_["clauses"],
            "order_by": None,
        }

        if filter.sort:
            res["order_by"], order_by_relationships = cls.get_order_by(collection, filter)
            res["relationships"] = merge_relationships(res["relationships"], order_by_relationships)
        return res


class QueryFactoryException(DatasourceToolkitException):
    pass


class QueryFactory:
    @classmethod
    def _build_list(
        cls,
        collection: BaseSqlAlchemyCollection,
        filter: Optional[PaginatedFilter],
        columns: List[SqlAlchemyColumn],
        relationships: Optional[Relationships] = None,
    ):
        if not relationships:
            relationships = defaultdict(list)
        query: Any = select(*columns).select_from(collection.mapper)
        if filter:
            options = PaginatedFilterFactory.build(collection, filter)
            relationships = merge_relationships(relationships, options.get("relationships", {}))
            if options.get("clauses") is not None:
                query = query.where(options["clauses"])
            if options.get("order_by"):
                query = query.order_by(*options.get("order_by"))

            if filter.page:
                query = query.limit(filter.page.limit).offset(filter.page.skip)

        for level in sorted(relationships.keys()):
            for relationship in relationships[level]:
                query = query.join(*relationship, isouter=True)
        return query

    @classmethod
    def build_list(
        cls,
        collection: BaseSqlAlchemyCollection,
        filter: PaginatedFilter,
        projection: Projection,
    ):
        if collection.mapper:
            columns, relationships = collection.get_columns(projection)
            return cls._build_list(collection, filter, columns, relationships)  # type: ignore
        raise QueryFactoryException("Unable to request a collection without mapper")

    @classmethod
    def build_aggregate(
        cls,
        dialect: Dialect,
        collection: BaseSqlAlchemyCollection,
        filter: Optional[Filter],
        aggregation: Aggregation,
        limit: Optional[int],
    ):
        if collection.mapper:
            column, relationships = AggregationFactory.build_column(collection, aggregation)
            _filter = None
            if filter is not None:
                _filter = PaginatedFilter.from_base_filter(filter)
            groups, group_relationships = AggregationFactory.build_group(dialect, collection, aggregation)
            query = cls._build_list(
                collection,
                _filter,
                [column, *groups],
                merge_relationships(relationships, group_relationships),
            )
            if groups:
                query = query.group_by(*groups)

            if dialect.name == "postgresql":
                query = query.order_by(column.desc().nulls_last())
            else:
                query = query.order_by(column.desc())

            if limit:
                query = query.limit(limit)
            return query

    @staticmethod
    def update(
        collection: BaseSqlAlchemyCollection,
        filter: Optional[Filter],
        patch: RecordsDataAlias,
    ):
        if collection.model:
            options: FilterOptions = FilterFactory.build(collection, filter)
            query = update(collection.model).values(**patch)
            if options["clauses"] is not None:
                query = query.where(options["clauses"])
            return query.execution_options(synchronize_session="fetch")
        raise QueryFactoryException("Unable to request a collection without mapper")

    @staticmethod
    def create(collection: BaseSqlAlchemyCollection, data: List[RecordsDataAlias]):
        if collection.model:
            instances: List[Any] = []
            for record in data:
                instances.append(collection.factory.init_instance(record))
            return instances
        raise QueryFactoryException("Unable to request a collection without mapper")

    @staticmethod
    def delete(collection: BaseSqlAlchemyCollection, filter: Optional[Filter]):
        if collection.model:
            options: FilterOptions = FilterFactory.build(collection, filter)
            query = delete(collection.model)
            if options["clauses"] is not None:
                query = query.where(options["clauses"])
            return query.execution_options(synchronize_session="fetch")
        raise QueryFactoryException("Unable to request a collection without mapper")
