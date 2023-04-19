from collections import defaultdict
from typing import Callable, List, Tuple

from forestadmin.datasource_sqlalchemy.interfaces import BaseSqlAlchemyCollection
from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships, merge_relationships
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, Aggregator, DateOperation
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from sqlalchemy import DATE, cast
from sqlalchemy import column as SqlAlchemyColumn
from sqlalchemy import func, text
from sqlalchemy.engine import Dialect


class AggregationFactoryException(DatasourceToolkitException):
    pass


class AggregationFactory:
    LABEL = "__aggregate__"
    GROUP_LABEL = "__grouped__"

    MAPPING = {
        Aggregator.COUNT: func.count,
        Aggregator.MIN: func.min,
        Aggregator.MAX: func.max,
        Aggregator.AVG: func.avg,
        Aggregator.SUM: func.sum,
    }

    @staticmethod
    def get_func(aggregation: Aggregation) -> Callable[[str], SqlAlchemyColumn]:
        try:
            return AggregationFactory.MAPPING[aggregation.operation]
        except KeyError:
            raise AggregationFactoryException(f'Unknown aggregator "{aggregation.operation}"')

    @classmethod
    def get_group_field_name(cls, field_name: str):
        return f"{field_name}{cls.GROUP_LABEL}"

    @classmethod
    def get_field_from_group_field_name(cls, group_field_name: str):
        return group_field_name[: -len(cls.GROUP_LABEL)]

    @staticmethod
    def get_field(collection: BaseSqlAlchemyCollection, aggregation: Aggregation) -> Tuple[str, Relationships]:
        field = "*"
        relationships: Relationships = defaultdict(list)
        if aggregation.field:
            fields, relationships = collection.get_columns(Projection(aggregation.field))
            field = fields[0]
        return field, relationships

    @classmethod
    def build_column(cls, collection: BaseSqlAlchemyCollection, aggregation: Aggregation) -> SqlAlchemyColumn:
        func = cls.get_func(aggregation)
        field, relationships = cls.get_field(collection, aggregation)
        return func(field).label(cls.LABEL), relationships

    @classmethod
    def build_group(
        cls,
        dialect: Dialect,
        collection: BaseSqlAlchemyCollection,
        aggregation: Aggregation,
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        groups: List[SqlAlchemyColumn] = []
        group_relationships: Relationships = defaultdict(list)
        for group in aggregation.groups:
            columns, relationships = collection.get_columns(Projection(group["field"]))
            operation = group.get("operation")
            if operation:
                column = DateAggregation.build(dialect, columns[0], operation)
            else:
                column = columns[0]
            groups.append(column.label(cls.get_group_field_name(group["field"])))
            group_relationships = merge_relationships(relationships, group_relationships)
        return groups, group_relationships


class DateAggregation:
    @staticmethod
    def build_postgres(column: SqlAlchemyColumn, operation: DateOperation) -> SqlAlchemyColumn:
        return func.date_trunc(operation.value.lower(), column)

    @staticmethod
    def build_sqllite(column: SqlAlchemyColumn, operation: DateOperation) -> SqlAlchemyColumn:
        if operation == DateOperation.WEEK:
            return func.DATE(column, "weekday 1", "-7 days")
        elif operation == DateOperation.YEAR:
            format = "%Y-01-01"
        elif operation == DateOperation.MONTH:
            format = "%Y-%m-01"
        elif operation == DateOperation.DAY:
            format = "%Y-%m-%d"
        else:
            raise AggregationFactoryException()
        return func.strftime(format, column)

    @staticmethod
    def build_mysql(column: SqlAlchemyColumn, operation: DateOperation) -> SqlAlchemyColumn:
        format = "%Y-%m-%d"
        if operation == DateOperation.YEAR:
            format = "%Y-01-01"
        elif operation == DateOperation.MONTH:
            format = "%Y-%m-01"
        elif operation == DateOperation.WEEK:
            return cast(func.date_sub(column, text(f"INTERVAL(WEEKDAY({column})) DAY")), DATE)
        elif operation == DateOperation.DAY:
            format = "%Y-%m-%d"
        else:
            raise AggregationFactoryException()
        return func.date_format(column, format)

    @staticmethod
    def build_mssql(column: SqlAlchemyColumn, operation: DateOperation) -> SqlAlchemyColumn:
        if operation == DateOperation.YEAR:
            return func.datefromparts(func.extract("year", column), "01", "01")
        elif operation == DateOperation.MONTH:
            return func.datefromparts(func.extract("year", column), func.extract("month", column), "01")
        elif operation == DateOperation.WEEK:
            return cast(func.dateadd(text("day"), -func.extract("dw", column) + 2, column), DATE)
        elif operation == DateOperation.DAY:
            return func.datefromparts(
                func.extract("year", column),
                func.extract("month", column),
                func.extract("day", column),
            )

    @classmethod
    def build(cls, dialect: Dialect, column: SqlAlchemyColumn, operation: DateOperation) -> SqlAlchemyColumn:
        if dialect.name == "sqlite":
            return cls.build_sqllite(column, operation)
        elif dialect.name in ["mysql", "mariadb"]:
            return cls.build_mysql(column, operation)
        elif dialect.name == "postgresql":
            return cls.build_postgres(column, operation)
        elif dialect.name == "mssql":
            return cls.build_mssql(column, operation)
        else:
            raise AggregationFactoryException(f"The dialect {dialect.name} is not handled")
