import os
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from sqlalchemy import select
from src.config import settings
from src.database import get_session
from src.with_sql_alchemy.models import Address, Customer

app = FastAPI(
    debug=settings.debug,
)

COLLECTION_NAME_TO_MODEL: Dict[str, Any] = {
    "Address": Address,
    "Customer": Customer,
}


@app.get("/")
async def root():
    with get_session()().begin() as session:
        items = session.session.scalars(select(Address).limit(15))
        return [i.__dict__ for i in items]


@app.get(
    "/{collection}/",
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
