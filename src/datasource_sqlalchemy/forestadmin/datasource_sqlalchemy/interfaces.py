import abc
from typing import Any, Callable, List, Optional, Tuple

from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from sqlalchemy import Table
from sqlalchemy import column as SqlAlchemyColumn
from sqlalchemy.orm import Mapper
from typing_extensions import Self


class BaseSqlAlchemyCollectionFactory(abc.ABC):
    @abc.abstractmethod
    def init_instance(self, data: RecordsDataAlias) -> "BaseSqlAlchemyCollection":
        """instantiate model class from raw data"""


class BaseSqlAlchemyCollection(Collection, abc.ABC):
    @abc.abstractmethod
    def get_column(self, name: str) -> Self:
        """return column name 'name'"""

    @abc.abstractmethod
    def _get_related_column(
        self, projection: Projection, level: int = 0
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        """return (columns, relationships)"""

    @abc.abstractmethod
    def get_columns(self, projection: Projection, level: int = 0) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        """return (columns, relationships)"""

    @abc.abstractproperty
    def table(self) -> Table:  # type: ignore
        """return table of this collection"""

    @abc.abstractproperty
    def mapper(self) -> Optional[Mapper]:
        """return table mapper"""

    @abc.abstractproperty
    def model(self) -> Optional[Callable[[Any], Any]]:
        """return model of the collection"""

    @abc.abstractproperty
    def factory(self) -> BaseSqlAlchemyCollectionFactory:  # type: ignore
        """return collection factory"""


class BaseSqlAlchemyDatasource(Datasource[Collection], abc.ABC):
    pass
