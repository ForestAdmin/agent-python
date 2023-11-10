import abc

from django.db.models import Model
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from typing_extensions import Self

# class BaseDjangoCollectionFactory(abc.ABC):
#     @abc.abstractmethod
#     def init_instance(self, data: RecordsDataAlias) -> "BaseSqlAlchemyCollection":
#         """instantiate model class from raw data"""


class BaseDjangoCollection(Collection, abc.ABC):
    @abc.abstractmethod
    def get_column(self, name: str) -> Self:
        """return column name 'name'"""

    # @abc.abstractmethod
    # def _get_related_column(
    #     self, projection: Projection, level: int = 0
    # ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
    #     """return (columns, relationships)"""

    # @abc.abstractmethod
    # def get_columns(self, projection: Projection, level: int = 0) -> Tuple[List[DjangoColumn], Relationships]:
    #     """return (columns, relationships)"""

    # @abc.abstractproperty
    # def table(self) -> Table:  # type: ignore
    #     """return table of this collection"""

    # @abc.abstractproperty
    # def mapper(self) -> Optional[Mapper]:
    #     """return table mapper"""

    @abc.abstractproperty
    def model(self) -> Model:
        """return model of the collection"""

    # @abc.abstractproperty
    # def factory(self) -> BaseDjangoCollectionFactory:  # type: ignore
    #     """return collection factory"""


class BaseDjangoDatasource(Datasource, abc.ABC):
    pass
