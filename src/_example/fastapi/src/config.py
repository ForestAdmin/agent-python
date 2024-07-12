import os
from functools import lru_cache

from dotenv import load_dotenv
from forestadmin.fastapi_agent.settings import ForestFastAPISettings
from pydantic_settings import BaseSettings

load_dotenv()  # load .env file into environ variables


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    app_name: str = "Example API"
    debug: bool = os.environ.get("FASTAPI_DEBUG", "False").lower() == "true"
    # db_uri: str = f'sqlite+aiosqlite:///{os.path.abspath(os.path.join(__file__, "..", "..", "db.sql"))}'
    db_uri: str = f'sqlite:///{os.path.abspath(os.path.join(__file__, "..", "..", "db.sql"))}'


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_forest_settings() -> ForestFastAPISettings:
    return ForestFastAPISettings(
        auth_secret=os.environ.get("FOREST_AUTH_SECRET", "mandatory"),
        env_secret=os.environ.get("FOREST_ENV_SECRET", "mandatory"),
        schema_path=os.path.abspath(os.path.join(__file__, "..", ".forestadmin-schema.json")),
        server_url=os.environ.get("FOREST_SERVER_URL"),
        # prefix="/bla",
    )


settings: Settings = get_settings()
forest_settings: ForestFastAPISettings = get_forest_settings()
