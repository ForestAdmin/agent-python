from typing import Any, Awaitable, Callable

from forestadmin.datasource_toolkit.datasources import DatasourceException
from sqlalchemy.exc import SQLAlchemyError


class SqlAlchemyCollectionException(DatasourceException):
    pass


class SqlAlchemyDatasourceException(DatasourceException):
    pass


def handle_sqlalchemy_error(fn: Callable[..., Awaitable[Any]]):
    async def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(self, *args, **kwargs)
        except SQLAlchemyError as e:
            raise SqlAlchemyCollectionException(str(e))

    return wrapped
