from datetime import date, datetime
from unittest import TestCase

from forestadmin.datasource_toolkit.decorators.chart.result_builder import ResultBuilder
from forestadmin.datasource_toolkit.interfaces.query.aggregation import DateOperation


class TestResultBuilderValue(TestCase):
    def test_value_should_return_correct_format(self):
        ResultBuilder.value(42) == {"countCurrent": 42, "countPrevious": None}
        ResultBuilder.value(42, 34) == {"countCurrent": 42, "countPrevious": 34}


class TestResultBuilderDistribution(TestCase):
    def test_distribution_should_return_correct_format(self):
        self.assertEqual(
            ResultBuilder.distribution({"a": 10, "b": 11}), [{"key": "a", "value": 10}, {"key": "b", "value": 11}]
        )


class TestResultBuilderPercentage(TestCase):
    def test_percentage_should_return_correct_format(self):
        result = ResultBuilder.percentage(42)
        assert result == 42


class TestResultBuilderObjective(TestCase):
    def test_objective_should_return_correct_format(self):
        result = ResultBuilder.objective(42, 54)
        assert result == {"value": 42, "objective": 54}


class TestResultBuilderLeaderBoard(TestCase):
    def test_leaderboard_should_return_correct_format(self):
        result = ResultBuilder.leaderboard({"a": 10, "b": 30, "c": 20})
        assert result == [{"key": "a", "value": 10}, {"key": "c", "value": 20}, {"key": "b", "value": 30}]


class TestResultBuilderSmart(TestCase):
    def test_smart_return_expected_format(self):
        result = ResultBuilder.smart(42)
        assert result == 42


class TestResultBuilderTimeBased(TestCase):
    def test_time_based_should_return_correct_format_day_from_string(self):
        self.assertEqual(
            ResultBuilder.time_based(
                DateOperation.DAY,
                {
                    "1985-10-27": 2,
                    "1985-10-26": 1,
                    "1985-10-30": 3,
                },
            ),
            [
                {"label": "26/10/1985", "values": {"value": 1}},
                {"label": "27/10/1985", "values": {"value": 2}},
                {"label": "28/10/1985", "values": {"value": 0}},
                {"label": "29/10/1985", "values": {"value": 0}},
                {"label": "30/10/1985", "values": {"value": 3}},
            ],
        )

    def test_time_based_should_return_correct_format_day_from_date(self):
        assert ResultBuilder.time_based(
            DateOperation.DAY,
            {
                date(1985, 10, 27): 2,
                date(1985, 10, 26): 1,
                date(1985, 10, 30): 3,
            },
        ) == [
            {"label": "26/10/1985", "values": {"value": 1}},
            {"label": "27/10/1985", "values": {"value": 2}},
            {"label": "28/10/1985", "values": {"value": 0}},
            {"label": "29/10/1985", "values": {"value": 0}},
            {"label": "30/10/1985", "values": {"value": 3}},
        ]

    def test_time_based_should_return_correct_format_day_from_datetime(self):
        assert ResultBuilder.time_based(
            DateOperation.DAY,
            {
                datetime(1985, 10, 27): 2,
                datetime(1985, 10, 26): 1,
                datetime(1985, 10, 30): 3,
            },
        ) == [
            {"label": "26/10/1985", "values": {"value": 1}},
            {"label": "27/10/1985", "values": {"value": 2}},
            {"label": "28/10/1985", "values": {"value": 0}},
            {"label": "29/10/1985", "values": {"value": 0}},
            {"label": "30/10/1985", "values": {"value": 3}},
        ]

    def test_time_based_should_return_correct_format_week(self):
        result = ResultBuilder.time_based(
            DateOperation.WEEK,
            {
                "1985-12-26": 1,
                "1986-01-08": 4,
                "1986-01-07": 3,
            },
        )
        assert result == [
            {"label": "W52-1985", "values": {"value": 1}},
            {"label": "W01-1986", "values": {"value": 0}},
            {"label": "W02-1986", "values": {"value": 7}},
        ]

    def test_time_based_should_return_correct_format_month(self):
        result = ResultBuilder.time_based(
            DateOperation.MONTH,
            {
                "1985-10-26": 1,
                "1985-11-27": 2,
                "1986-01-07": 3,
                "1986-01-08": 4,
            },
        )
        assert result == [
            {"label": "Oct 1985", "values": {"value": 1}},
            {"label": "Nov 1985", "values": {"value": 2}},
            {"label": "Dec 1985", "values": {"value": 0}},
            {"label": "Jan 1986", "values": {"value": 7}},
        ]

    def test_time_based_should_return_correct_format_year(self):
        result = ResultBuilder.time_based(
            DateOperation.YEAR,
            {
                "1985-12-26": 1,
                "1986-01-08": 4,
                "1986-01-07": 3,
            },
        )
        assert result == [{"label": "1985", "values": {"value": 1}}, {"label": "1986", "values": {"value": 7}}]


class TestResultBuilderMultiTimeBased(TestCase):
    def test_should_return_labels_and_key_value_for_each_line(self):
        result = ResultBuilder.multiple_time_based(
            DateOperation.YEAR,
            [
                "1985-10-25",
                "1986-01-07",
                "1986-01-08",
                "1985-10-27",
            ],
            [{"label": "firstLine", "values": [1, 2, 3, None]}, {"label": "secondLine", "values": [4, 2, 6, 7]}],
        )
        self.assertEqual(
            result,
            {
                "labels": ["1985", "1986"],
                "values": [
                    {"key": "firstLine", "values": [1, 5]},
                    {"key": "secondLine", "values": [11, 8]},
                ],
            },
        )

    def test_should_display_zero_values_when_there_are_only_null_values_for_a_time_range(self):
        result = ResultBuilder.multiple_time_based(
            DateOperation.YEAR,
            [
                "1985-10-25",
                "1986-01-07",
                "1986-01-08",
                "1985-10-27",
            ],
            [{"label": "firstLine", "values": [None, 2, 3, None]}],
        )
        self.assertEqual(
            result,
            {
                "labels": ["1985", "1986"],
                "values": [
                    {"key": "firstLine", "values": [0, 5]},
                ],
            },
        )

    def test_should_display_number_when_there_is_number_and_none_values_for_a_time_range(self):
        result = ResultBuilder.multiple_time_based(
            DateOperation.YEAR,
            [
                "1985-10-25",
                "1986-01-07",
                "1986-01-08",
                "1985-10-27",
            ],
            [{"label": "firstLine", "values": [100, 1.3, 2.5, None]}],
        )
        self.assertEqual(
            result,
            {
                "labels": ["1985", "1986"],
                "values": [
                    {"key": "firstLine", "values": [100, 3.8]},
                ],
            },
        )

    def test_should_raise_exception_when_giving_a_not_iso_string_date_format(self):
        self.assertRaisesRegex(
            ValueError,
            r"Invalid isoformat string: '08-01-1986'",
            ResultBuilder.multiple_time_based,
            DateOperation.YEAR,
            [
                "1985-10-25",
                "1986-01-07",
                "08-01-1986",
                "1985-10-27",
            ],
            [{"label": "firstLine", "values": [100, 1, 2, None]}],
        )
