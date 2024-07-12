from demo.models.models import DB_URI, Base
from sqlalchemy import create_engine


def create_all():
    engine = create_engine(DB_URI, echo=False)
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
