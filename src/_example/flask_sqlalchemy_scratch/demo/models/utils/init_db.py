from demo.models.models import Base


def create_all():
    Base.metadata.create_all()
