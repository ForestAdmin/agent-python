from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from src.config import settings

try:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
except Exception:
    async_sessionmaker = None
    create_async_engine = None

# use_sqlalchemy_2 = sqlalchemy.__version__.split(".")[0] == "2"
# if use_sqlalchemy_2:
# else:
#     from sqlalchemy import create_engine
#     from sqlalchemy.orm import declarative_base
#     Base = declarative_base()


class Base(DeclarativeBase):
    pass


def get_session():
    engine = create_engine(settings.db_uri)
    Session = sessionmaker(engine)
    return Session


if async_sessionmaker is not None and create_async_engine is not None:

    def aget_session():
        engine = create_async_engine(settings.db_uri)
        Session = async_sessionmaker(engine)
        return Session

else:

    def aget_session():
        return get_session()
