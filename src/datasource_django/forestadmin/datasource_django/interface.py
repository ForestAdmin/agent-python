import abc

from django.db.models import Model
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource


class BaseDjangoCollection(Collection, abc.ABC):
    def model(self) -> Model:
        """return model of the collection"""


class BaseDjangoDatasource(Datasource, abc.ABC):
    pass
