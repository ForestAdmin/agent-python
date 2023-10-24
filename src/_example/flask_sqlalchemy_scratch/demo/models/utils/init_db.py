from demo.models.models import SQLITE_URI, Base
from sqlalchemy import create_engine


def create_all():
    engine = create_engine(SQLITE_URI, echo=False)
    with engine.begin() as conn:
        Base.metadata.create_all(conn)

    # Base.metadata.create_all(SQLITE_URI)
