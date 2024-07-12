import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from forestadmin.datasource_sqlalchemy.datasource import SqlAlchemyDatasource
from forestadmin.fastapi_agent.agent import create_agent
from src.config import forest_settings, settings
from src.custom_logs import ColorizedFormatter
from src.forest.agent import customize_forest
from src.sql_alchemy.models import Base

forest_logger = logging.getLogger("forestadmin")

app = FastAPI(debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https:\/\/.*\.forestadmin.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["authorization"],
)

agent = create_agent(app, forest_settings)
agent.add_datasource(SqlAlchemyDatasource(Base, settings.db_uri))
customize_forest(agent)
# asyncio.run(agent.start())  # agent.start is launch by fastapi (app.add_event_handler("startup", agent.start))

forest_logger.setLevel(logging.DEBUG)

for h in forest_logger.handlers:
    h.setLevel(logging.DEBUG)
    h.setFormatter(ColorizedFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"))


if __name__ == "__main__":
    print(os.environ.get("FASTAPI_APP", "main:app"))
    uvicorn.run(
        app=app,  # os.environ.get("FASTAPI_APP", "main:app"),
        host=os.environ.get("FASTPI_HOST", "0.0.0.0"),
        port=int(os.environ.get("FASTPI_PORT", "8000")),
    )
