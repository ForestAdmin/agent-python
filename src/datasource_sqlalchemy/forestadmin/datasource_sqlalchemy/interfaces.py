import abc
from typing import Any, Callable, List, Optional, Tuple

from forestadmin.datasource_sqlalchemy.utils.relationships import Relationships
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from sqlalchemy import Table
from sqlalchemy import column as SqlAlchemyColumn
from sqlalchemy.orm import Mapper
from typing_extensions import Self


class BaseSqlAlchemyCollectionFactory(abc.ABC):
    @abc.abstractmethod
    def init_instance(self, data: RecordsDataAlias) -> "BaseSqlAlchemyCollection":
        pass


class BaseSqlAlchemyCollection(Collection, abc.ABC):
    @abc.abstractmethod
    def get_column(self, name: str) -> Self:
        pass

    @abc.abstractmethod
    def _get_related_column(
        self, projection: Projection, level: int = 0
    ) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        pass

    @abc.abstractmethod
    def get_columns(self, projection: Projection, level: int = 0) -> Tuple[List[SqlAlchemyColumn], Relationships]:
        pass

    @abc.abstractproperty
    def table(self) -> Table:  # type: ignore
        pass

    @abc.abstractproperty
    def mapper(self) -> Optional[Mapper]:
        pass

    @abc.abstractproperty
    def model(self) -> Optional[Callable[[Any], Any]]:
        pass

    @abc.abstractproperty
    def factory(self) -> BaseSqlAlchemyCollectionFactory:  # type: ignore
        pass
