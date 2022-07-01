import asyncio
import enum

from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregator as AggregationOperation
from forestadmin.datasource_toolkit.interfaces.query.aggregation import DateOperation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, create_engine, func
from sqlalchemy.orm import backref, declarative_base, relationship

# engine = create_engine("sqlite:///:memory:", echo=True)

# pip install pymysql
# docker run --name some-mysql -p 3306:3306 -e MYSQL_DATABASE=db_test -e MYSQL_ROOT_PASSWORD=my-secret-pw -d mysql
# engine = create_engine("mysql+pymysql://root:my-secret-pw@localhost:3306/db_test", echo=True)

# pip install pymysql
# docker run --name some-mariadb -p 3808:3306 -e MYSQL_DATABASE=db_test -e MYSQL_ROOT_PASSWORD=my-secret-pw -d mariadb
# engine = create_engine("mariadb+pymysql://root:my-secret-pw@localhost:3808/db_test", echo=True)

# pip install psycopg2
# docker run --name some-postgres -e POSTGRES_DB=db_test -e POSTGRES_PASSWORD=my-secret-pw \
# -e POSTGRES_USER=root -p 5467:5432 -d postgres
engine = create_engine("postgresql://root:my-secret-pw@localhost:5467/db_test", echo=True)

# docker run --name some-mssql -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong_Passw0rd" \
# -p 1433:1433 -d mcr.microsoft.com/mssql/server:2019-latest
# docker exec -it some-mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "YourStrong_Passw0rd"
# CREATE DATABASE db_test GO
# brew uninstall --force freetds
# brew install freetds@0.91
# brew link --force freetds@0.91
# pip install pymssql
# engine = create_engine('mssql+pymssql://SA:YourStrong_Passw0rd@localhost:1433/db_test', echo=True)

Base = declarative_base(bind=engine)


class Gender(enum.Enum):
    M = "M1"
    F = "F2"


association_table = Table(
    "association",
    Base.metadata,
    Column("child_id", ForeignKey("child.id"), primary_key=True),
    Column("parent_id", ForeignKey("parent.id"), primary_key=True),
)


class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    first_name = Column(String(254), nullable=False)
    gender = Column(Enum(Gender))
    parent = relationship("Parent", secondary="association", back_populates="children")


class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(254), nullable=False)
    age = Column(Integer)
    children = relationship("Child", secondary="association", back_populates="parent")
    company_id = Column(Integer, ForeignKey("company.id"))
    company = relationship("Company", backref="parents")


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    name = Column(String(254), nullable=False)


class Place(Base):
    __tablename__ = "place"
    id = Column(Integer, primary_key=True)
    address = Column(String(254), nullable=False)
    company_id = Column(Integer, ForeignKey("company.id"))
    company = relationship("Company", backref=backref("place", uselist=False))


async def main():
    Base.metadata.create_all()
    datasource = SqlAlchemyDatasource(Base)

    projection = Projection("id", "first_name", "parent:first_name", "parent:id")
    filter = PaginatedFilter(
        {
            "condition_tree": ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeBranch(
                        aggregator=Aggregator.OR,
                        conditions=[
                            ConditionTreeLeaf(
                                field="first_name",
                                operator=Operator.EQUAL,
                                value="valentin",
                            ),
                            ConditionTreeLeaf(field="id", operator=Operator.NOT_EQUAL, value="1"),
                        ],
                    ),
                    ConditionTreeLeaf(
                        field="parent:first_name",
                        operator=Operator.NOT_EQUAL,
                        value="1",
                    ),
                    ConditionTreeLeaf(field="parent:id", operator=Operator.EQUAL, value="1"),
                ],
            ),
            "sort": Sort([{"field": "parent:company:id", "ascending": False}]),
            "page": Page(limit=10, skip=20),
        }
    )

    child_collection = datasource.get_collection("child")
    print(child_collection.schema["fields"])
    res = await child_collection.list(filter, projection)
    print(res)

    await child_collection.create([{"age": 12, "first_name": "toto", "gender": "M"}])

    company_collection = datasource.get_collection("company")
    await company_collection.create(
        [
            {
                "name": "company1",
            },
            {
                "name": "company2",
            },
        ]
    )

    place_collection = datasource.get_collection("place")
    await place_collection.create([{"address": "12 av charles de gaulle", "company_id": 1}])
    await place_collection.create([{"address": "16 av de l'europe", "company_id": 1}])

    res = await place_collection.list(
        PaginatedFilter(
            {
                "sort": Sort(
                    [
                        {
                            "field": "id",
                            "ascending": False,
                        }
                    ]
                ),
                "page": Page(limit=2, skip=0),
            }
        ),
        Projection("id", "address", "company:name"),
    )
    print("prout", res)

    await place_collection.update(
        Filter({"condition_tree": ConditionTreeLeaf(field="address", operator=Operator.CONTAINS, value="charles")}),
        {"address": "test update"},
    )
    res = await place_collection.list(PaginatedFilter({}), Projection("id", "address", "company:name"))
    print(res)
    await place_collection.delete(
        Filter({"condition_tree": ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value="2")}),
    )
    res = await place_collection.list(PaginatedFilter({}), Projection("id", "address", "company:name"))
    print(res)
    res = await company_collection.list(
        PaginatedFilter(
            {
                "condition_tree": ConditionTreeLeaf(field="name", operator=Operator.EQUAL, value="company1"),
            }
        ),
        Projection("id", "name", "place:address"),
    )
    print(res)
    parent_collection = datasource.collections[2]
    await parent_collection.create([{"first_name": "toto", "company_id": "1"}])

    res = await child_collection.aggregate(
        Filter({"condition_tree": ConditionTreeLeaf(field="parent:id", operator=Operator.EQUAL, value="1")}),
        Aggregation(
            {
                "operation": AggregationOperation.COUNT,
                "groups": [
                    {
                        "field": "parent:company:created_at",
                        "operation": DateOperation.YEAR,
                    }
                ],
            }
        ),
        None,
    )
    print("hihi", res)

    res = await child_collection.aggregate(
        Filter(
            {
                "condition_tree": ConditionTreeLeaf(field="parent:company:id", operator=Operator.EQUAL, value="1"),
            }
        ),
        Aggregation(
            {
                "operation": AggregationOperation.AVG,
                "field": "parent:age",
            }
        ),
        None,
    )

    print(res, "\n\n\n")

    res = await company_collection.aggregate(
        Filter({}),
        Aggregation(
            {
                "operation": AggregationOperation.COUNT,
                "groups": [{"field": "created_at", "operation": DateOperation.DAY}],
            }
        ),
        1,
    )
    print(res)

    association_collection = datasource.collections[-1]
    res = await association_collection.list(PaginatedFilter({}), Projection("child_id", "parent_id"))
    print("\n\n\n", association_collection)

    # await association_collection.create([{'child_id': 1, 'parent_id': 2}])
    res = await association_collection.list(PaginatedFilter({}), Projection("child_id", "parent_id"))
    print(res)

    res = await FilterFactory.make_through_filter(
        child_collection,
        [1],
        "parent",
        PaginatedFilter(
            {"search": "a", "timezone": "UTC", "condition_tree": ConditionTreeLeaf("company_id", Operator.EQUAL, 1)}
        ),
    )
    print(res.condition_tree)

    res = await FilterFactory.make_foreign_filter(
        company_collection,
        [1],
        "parents",
        PaginatedFilter(
            {
                "timezone": "UTC",
            }
        ),
    )

    print("\n\n", res.condition_tree)


if __name__ == "__main__":
    asyncio.run(main())
