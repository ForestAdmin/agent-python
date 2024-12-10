import re

from forestadmin.datasource_toolkit.exceptions import NativeQueryException


class EmptySQLQueryException(NativeQueryException):
    def __init__(self, *args: object) -> None:
        super().__init__("You cannot execute an empty SQL query.")


class ChainedSQLQueryException(NativeQueryException):
    def __init__(self, *args: object) -> None:
        super().__init__("You cannot chain SQL queries.")


class NonSelectSQLQueryException(NativeQueryException):
    def __init__(self, *args: object) -> None:
        super().__init__("Only SELECT queries are allowed.")


class SqlQueryChecker:
    QUERY_SELECT = re.compile(r"^SELECT\s(.|\n)*FROM\s(.|\n)*$", re.IGNORECASE)

    @staticmethod
    def check_query(input_query: str) -> bool:
        input_query_trimmed = input_query.strip()

        if len(input_query_trimmed) == 0:
            raise EmptySQLQueryException()

        if ";" in input_query_trimmed and input_query_trimmed.index(";") != len(input_query_trimmed) - 1:
            raise ChainedSQLQueryException()

        if not SqlQueryChecker.QUERY_SELECT.match(input_query_trimmed):
            raise NonSelectSQLQueryException()

        return True
