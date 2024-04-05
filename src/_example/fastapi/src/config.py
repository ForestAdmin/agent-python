import os
from functools import lru_cache
from typing import Union

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()  # load .env file into environ variables


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    app_name: str = "Example API"
    debug: bool = os.environ.get("FASTAPI_DEBUG", "False").lower() == "true"
    # db_uri: str = f'sqlite+aiosqlite:///{os.path.abspath(os.path.join(__file__, "..", "..", "db.sql"))}'
    db_uri: str = f'sqlite:///{os.path.abspath(os.path.join(__file__, "..", "..", "db.sql"))}'

    forest_server_url: Union[str, None] = os.environ.get("FOREST_SERVER_URL", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
