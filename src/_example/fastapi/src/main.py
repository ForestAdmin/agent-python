import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.fastapi_agent.agent import create_agent
from sqlalchemy import select
from src.config import settings
from src.database import Base, get_session
from src.with_sql_alchemy.models import Address, Customer

app = FastAPI(
    debug=settings.debug,
    # lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https:\/\/.*\.forestadmin.com",
    allow_credentials=True,
    allow_methods="*",
    allow_headers="*",
)

agent = create_agent(app, settings.model_dump())
agent.add_datasource(SqlAlchemyDatasource(Base, settings.db_uri))


COLLECTION_NAME_TO_MODEL: Dict[str, Any] = {
    "Address": Address,
    "Customer": Customer,
}


# @app.get("/")
# async def root():
#     with get_session()().begin() as session:
#         items = session.session.scalars(select(Address).limit(15))
#         return [i.__dict__ for i in items]


@app.get(
    "/a/{collection}/",
)
async def list_collection(collection: str):
    with get_session()().begin() as session:
        items = session.session.scalars(select(Address))
        return [i.__dict__ for i in items]
    # async with aget_session().begin() as session:
    #     items = await session.scalars(select(COLLECTION_NAME_TO_MODEL[collection]))
    #     items = [i.__dict__ for i in items]
    #     for i in items:
    #         del i["_sa_instance_state"]
    #     return [i for i in items]


if __name__ == "__main__":
    print(os.environ.get("FASTAPI_APP", "main:app"))
    uvicorn.run(
        app,  # os.environ.get("FASTAPI_APP", "main:app"),
        host=os.environ.get("FASTPI_HOST", "0.0.0.0"),
        port=int(os.environ.get("FASTPI_PORT", "8000")),
    )
