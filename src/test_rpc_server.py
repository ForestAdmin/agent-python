from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.datasource_toolkit.interfaces.models.collections import JsonCollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

engine = create_engine("postgresql://root:my-secret-pw@localhost:5467/db_test", echo=True)
Base = declarative_base(bind=engine)


class Child(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    first_name = Column(String(254), nullable=False)


Base.metadata.create_all()
datasource = SqlAlchemyDatasource(Base)
app = FastAPI()


def filter_from_body(params: Dict[str, Any]) -> Filter:
    condition_tree: Optional[ConditionTree] = None

    filter = params.get("filter", {})
    if filter.get("condition_tree") or filter.get("conditionTree"):
        condition_tree = ConditionTreeFactory.from_plain_object(
            filter.get("condition_tree", filter.get("conditionTree"))
        )
    print(filter)
    return Filter(
        {
            "condition_tree": condition_tree,
            "search": filter.get("search"),
            "search_extended": filter.get("search_extended", False),
            "segment": filter.get("segment", ""),
            "timezone": filter.get("timezone", "utc"),
        }
    )


def paginated_filter_from_body(params: Dict[str, Any]) -> PaginatedFilter:
    page: Optional[Page] = None
    f = params.get("filter", {})
    sort: Sort = Sort(f.get("sort", []))
    filter = filter_from_body(params)

    if f.get("page"):
        page = Page(f["page"].get("int"), f["page"].get("limit"))

    return PaginatedFilter(
        {
            **filter.to_filter_component(),
            "page": page,
            "sort": sort,
        }
    )


def handshake():
    res = {}
    for collection in datasource.collections:
        res[collection.name] = JsonCollectionSchema.dumps(collection.schema)
    return {"dataSourceSchema": {}, "collectionSchemas": res}


async def list(collection_name: str, params: Dict[str, Any]):
    filter: PaginatedFilter = paginated_filter_from_body(params)
    collection = datasource.get_collection(collection_name)
    return await collection.list(filter, Projection(*params["projection"]))


async def create(collection_name: str, params: Dict[str, Any]):
    collection = datasource.get_collection(collection_name)
    return await collection.create(params["data"])


async def update(collection_name: str, params: Dict[str, Any]):
    collection = datasource.get_collection(collection_name)
    filter: Filter = filter_from_body(params)
    return await collection.update(filter, params["patch"])


async def delete(collection_name: str, params: Dict[str, Any]):
    collection = datasource.get_collection(collection_name)
    filter: Filter = filter_from_body(params)
    return await collection.delete(filter)


class Request(BaseModel):
    method: str
    collection: str = ""
    params: Dict[str, Any] = {}


@app.post("/")
async def main(request: Request):
    if request.method == "handshake":
        return JSONResponse(handshake())
    elif request.method == "list":
        return JSONResponse(await list(request.collection, request.params))
    elif request.method == "create":
        return JSONResponse(await create(request.collection, request.params))
    elif request.method == "update":
        return JSONResponse(await update(request.collection, request.params))
    elif request.method == "delete":
        return JSONResponse(await delete(request.collection, request.params))
