from unittest import TestCase

from forestadmin.agent_toolkit.utils.sql_query_checker import (
    ChainedSQLQueryException,
    EmptySQLQueryException,
    NonSelectSQLQueryException,
    SqlQueryChecker,
)


class TestSqlQueryChecker(TestCase):
    def test_normal_sql_query_should_be_ok(self):
        self.assertTrue(
            SqlQueryChecker.check_query(
                """
                Select status, sum(amount) as value
                from order
                where status != "rejected"
                group by status having status != "rejected";
                """
            )
        )

    def test_should_raise_on_linked_query(self):
        self.assertRaisesRegex(
            ChainedSQLQueryException,
            r"You cannot chain SQL queries\.",
            SqlQueryChecker.check_query,
            """
            Select status, sum(amount) as value
            from order
            where status != "rejected"
            group by status having status != "rejected"; delete from user_debts;
            """,
        )

    def test_should_raise_on_empty_query(self):
        self.assertRaisesRegex(
            EmptySQLQueryException,
            r"You cannot execute an empty SQL query\.",
            SqlQueryChecker.check_query,
            """

            """,
        )

    def test_should_raise_on_non_select_query(self):
        self.assertRaisesRegex(
            NonSelectSQLQueryException,
            r"Only SELECT queries are allowed\.",
            SqlQueryChecker.check_query,
            """
            delete from user_debts;
            """,
        )
