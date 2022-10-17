# pyright: reportPrivateUsage=false
from datetime import date
from unittest import mock

import pytest
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation, Aggregator, DateOperation, Summary
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


@pytest.mark.parametrize(
    "key,value",
    (
        ("COUNT", "Count"),
        ("SUM", "Sum"),
        ("AVG", "Avg"),
        ("MAX", "Max"),
        ("MIN", "Min"),
    ),
)
def test_aggregator(key: str, value: str):
    assert Aggregator[key].value == value


@pytest.mark.parametrize(
    "key,value",
    (
        ("YEAR", "Year"),
        ("MONTH", "Month"),
        ("WEEK", "Week"),
        ("DAY", "Day"),
    ),
)
def test_date_operation(key: str, value: str):
    assert DateOperation[key].value == value


def test_aggregation_init():
    aggregation = Aggregation(
        {
            "operation": "Count",
        }
    )
    assert aggregation.field is None
    assert aggregation.operation == Aggregator.COUNT
    assert aggregation.groups == []

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
        }
    )
    assert aggregation.field == "stock"
    assert aggregation.operation == Aggregator.SUM
    assert aggregation.groups == []

    aggregation = Aggregation({"field": "stock", "operation": "Sum", "groups": []})
    assert aggregation.field == "stock"
    assert aggregation.operation == Aggregator.SUM
    assert aggregation.groups == []

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
            "groups": [{"field": "updated_at", "operation": DateOperation.MONTH.value}],
        }
    )
    assert aggregation.field == "stock"
    assert aggregation.operation == Aggregator.SUM
    assert aggregation.groups == [{"field": "updated_at", "operation": DateOperation.MONTH}]


def test_projection():

    aggregation = Aggregation(
        {
            "operation": "Count",
        }
    )
    assert aggregation.projection == Projection()

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
        }
    )
    assert aggregation.projection == Projection("stock")

    aggregation = Aggregation(
        {
            "field": None,
            "operation": "Count",
            "groups": [{"field": "updated_at", "operation": DateOperation.MONTH.value}],
        }
    )
    assert aggregation.projection == Projection("updated_at")

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
            "groups": [{"field": "updated_at", "operation": DateOperation.MONTH.value}],
        }
    )
    assert aggregation.projection == Projection("stock", "updated_at")


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._format_summaries")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._create_summaries")
def test_apply(create_mock: mock.Mock, format_mock: mock.Mock):
    create_mock.return_value = "create_summary"
    format_mock.return_value = "format_summary"

    aggregation = Aggregation(
        {
            "operation": "Count",
        }
    )
    records = [{"id": 1}]
    tz = "UTC"

    assert aggregation.apply(records, tz) == "format_summary"
    format_mock.assert_called_once_with("create_summary")
    create_mock.assert_called_once_with(records, tz)


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._prefix_handler")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation.replace_fields")
def test_nest(replace_fields_mock: mock.Mock, prefix_handler_mock: mock.Mock):

    aggregation = Aggregation(
        {
            "field": "id",
            "operation": "Count",
        }
    )

    assert aggregation.nest("") == aggregation
    prefix_handler_mock.assert_not_called()
    replace_fields_mock.assert_not_called()

    aggregation = Aggregation(
        {
            "operation": "Count",
        }
    )
    assert aggregation.nest("prefix") == aggregation
    prefix_handler_mock.assert_not_called()
    replace_fields_mock.assert_not_called()

    aggregation = Aggregation(
        {
            "field": "id",
            "operation": "Count",
        }
    )
    prefix_handler_mock.return_value = "fake_handler"
    replace_fields_mock.return_value = "fake_replace_fields"
    assert aggregation.nest("prefix") == "fake_replace_fields"
    replace_fields_mock.assert_called_once_with("fake_handler")
    prefix_handler_mock.assert_called_once_with("prefix")


def test_replace_fields():
    def _handler(field: str) -> str:
        return f"{field}_suffix"

    aggregation = Aggregation(
        {
            "field": "id",
            "operation": "Count",
        }
    )
    assert aggregation.replace_fields(_handler) == Aggregation({"field": "id_suffix", "operation": "Count"})

    aggregation = Aggregation(
        {
            "operation": "Count",
            "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
        }
    )
    assert aggregation.replace_fields(_handler) == Aggregation(
        {
            "operation": "Count",
            "groups": [{"field": "created_at_suffix", "operation": DateOperation.YEAR.value}],
        }
    )

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
            "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
        }
    )
    assert aggregation.replace_fields(_handler) == Aggregation(
        {
            "field": "stock_suffix",
            "operation": "Sum",
            "groups": [{"field": "created_at_suffix", "operation": DateOperation.YEAR.value}],
        }
    )


def test_to_plain():
    aggregation = Aggregation({"operation": "Count"})
    assert aggregation._to_plain == {
        "operation": "Count",
        "field": None,
        "groups": [],
    }

    aggregation = Aggregation(
        {
            "field": "id",
            "operation": "Count",
        }
    )
    assert aggregation._to_plain == {
        "operation": "Count",
        "field": "id",
        "groups": [],
    }

    aggregation = Aggregation(
        {
            "field": "stock",
            "operation": "Sum",
            "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
        }
    )
    assert aggregation._to_plain == {
        "field": "stock",
        "operation": "Sum",
        "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
    }


def test_format_summaries():

    aggregation = Aggregation({"field": "price", "operation": "Avg"})

    summaries = [
        Summary(
            group={},
            start_count=0,
            Count=0,
            Sum=0,
            Max=0,
            Min=0,
        )
    ]
    assert aggregation._format_summaries(summaries) == []

    summaries.append(
        Summary(
            group={},
            start_count=0,
            Count=2,
            Sum=10,
            Max=0,
            Min=0,
        )
    )

    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 5}]

    summaries = [Summary(group={}, start_count=12, Count=3, Sum=2, Max=1, Min=5)]
    aggregation = Aggregation({"operation": "Count"})
    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 12}]

    aggregation = Aggregation({"field": "id", "operation": "Count"})
    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 3}]

    aggregation = Aggregation({"field": "id", "operation": "Sum"})
    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 2}]

    aggregation = Aggregation({"field": "id", "operation": "Max"})
    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 1}]

    aggregation = Aggregation({"field": "id", "operation": "Min"})
    assert aggregation._format_summaries(summaries) == [{"group": {}, "value": 5}]


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._create_group")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._create_summary")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._update_summary_in_place")
def test_create_summaries(
    update_summary_in_place_mock: mock.Mock,
    create_summary_mock: mock.Mock,
    create_group_mock: mock.Mock,
):

    tz = "UTC"
    records = [
        {"id": 1, "created_at": date.fromisoformat("2022-01-02")},
        {"id": 2, "created_at": date.fromisoformat("2021-12-23")},
        {"id": 3, "created_at": date.fromisoformat("2022-08-11")},
    ]

    aggregation = Aggregation(
        {
            "operation": "Count",
            "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
        }
    )

    create_group_results = [
        {"created_at": date.fromisoformat("2022-01-01")},
        {"created_at": date.fromisoformat("2021-01-01")},
        {"created_at": date.fromisoformat("2022-01-01")},
    ]
    create_group_mock.side_effect = create_group_results

    create_summary_results = [
        {
            "group": {"created_at": date.fromisoformat("2022-01-01")},
            "start_count": 0,
            "Count": 0,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
        {
            "group": {"created_at": date.fromisoformat("2021-01-01")},
            "start_count": 0,
            "Count": 0,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
    ]
    create_summary_mock.side_effect = create_summary_results

    update_summary_results = [
        {
            "group": {"created_at": date.fromisoformat("2022-01-01")},
            "start_count": 1,
            "Count": 1,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
        {
            "group": {"created_at": date.fromisoformat("2021-01-01")},
            "start_count": 1,
            "Count": 1,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
        {
            "group": {"created_at": date.fromisoformat("2022-01-01")},
            "start_count": 2,
            "Count": 2,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
    ]
    update_summary_in_place_mock.side_effect = update_summary_results

    assert aggregation._create_summaries(records, tz) == [
        {
            "group": {"created_at": date.fromisoformat("2022-01-01")},
            "start_count": 2,
            "Count": 2,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
        {
            "group": {"created_at": date.fromisoformat("2021-01-01")},
            "start_count": 1,
            "Count": 1,
            "Sum": 0,
            "Min": None,
            "Max": None,
        },
    ]
    create_group_mock.assert_has_calls(
        [
            mock.call(records[0], tz),
            mock.call(records[1], tz),
            mock.call(records[2], tz),
        ]
    )

    create_summary_mock.assert_has_calls([mock.call(create_group_results[0]), mock.call(create_group_results[1])])

    update_summary_in_place_mock.assert_has_calls(
        [
            mock.call(create_summary_results[0], records[0]),
            mock.call(create_summary_results[1], records[1]),
            mock.call(update_summary_results[0], records[2]),
        ]
    )


@pytest.mark.parametrize(
    "group",
    (
        {"id": 1, "created_at": date.fromisoformat("2022-01-02")},
        {"id": 2, "first_name": "test", "created_at": date.fromisoformat("2020-10-12")},
    ),
)
def test_create_summary(group: RecordsDataAlias):
    aggregation = Aggregation(
        {
            "operation": "Count",
            "groups": [{"field": "created_at", "operation": DateOperation.YEAR.value}],
        }
    )
    assert aggregation._create_summary(group) == {
        "group": group,
        "start_count": 0,
        "Count": 0,
        "Sum": 0,
        "Min": None,
        "Max": None,
    }


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.RecordUtils.get_field_value")
def test_update_summary_in_place(get_field_value_mock: mock.Mock):

    records = [
        {
            "id": 1,
            "stock": 12,
        },
        {
            "id": 2,
            "stock": 1,
        },
    ]

    summary: Summary = {
        "group": {},
        "start_count": 0,
        "Count": 0,
        "Sum": 0,
        "Min": None,
        "Max": None,
    }

    aggregation = Aggregation({"operation": "Count"})

    res = aggregation._update_summary_in_place(summary, records[0])
    assert res == {
        "group": {},
        "start_count": 1,
        "Count": 0,
        "Sum": 0,
        "Min": None,
        "Max": None,
    }
    get_field_value_mock.assert_not_called()

    res = aggregation._update_summary_in_place(summary, records[1])
    assert res == {
        "group": {},
        "start_count": 2,
        "Count": 0,
        "Sum": 0,
        "Min": None,
        "Max": None,
    }
    get_field_value_mock.assert_not_called()

    summary: Summary = {
        "group": {},
        "start_count": 0,
        "Count": 0,
        "Sum": 0,
        "Min": None,
        "Max": None,
    }
    get_field_value_mock.side_effect = [12, 1]
    aggregation = Aggregation({"operation": "Sum", "field": "stock"})

    res = aggregation._update_summary_in_place(summary, records[0])
    assert res == {
        "group": {},
        "start_count": 1,
        "Count": 1,
        "Sum": 12,
        "Min": 12,
        "Max": 12,
    }
    get_field_value_mock.assert_called_once_with(records[0], "stock")
    get_field_value_mock.reset_mock()

    res = aggregation._update_summary_in_place(summary, records[1])
    assert res == {
        "group": {},
        "start_count": 2,
        "Count": 2,
        "Sum": 13,
        "Min": 1,
        "Max": 12,
    }
    get_field_value_mock.assert_called_once_with(records[1], "stock")


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.RecordUtils.get_field_value")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.aggregation.Aggregation._apply_date_operation")
def test_create_group(apply_date_operation_mock: mock.Mock, get_field_value_mock: mock.Mock):
    records = [{"id": 1, "stock": 12, "cat": "cat1", "subcat": "subcat1"}]

    aggregation = Aggregation(
        {
            "operation": "Count",
            "groups": [{"field": "cat"}, {"field": "subcat"}],
        }
    )

    get_field_value_mock.side_effect = ["cat1", "subcat1"]
    apply_date_operation_mock.side_effect = ["cat1", "subcat1"]
    assert aggregation._create_group(records[0], "UTC") == {
        "cat": "cat1",
        "subcat": "subcat1",
    }


@pytest.mark.parametrize(
    "operation,expected",
    (
        (None, "2022-05-03T22:04:23.200Z"),
        (DateOperation.YEAR, "2022-01-01"),
        (DateOperation.MONTH, "2022-05-01"),
        (DateOperation.DAY, "2022-05-03"),
        (DateOperation.WEEK, "2022-05-02"),
    ),
)
def test_apply_date_operation(operation: DateOperation, expected: str):
    dt_iso = "2022-05-03T22:04:23.200Z"
    aggregation = Aggregation(
        {
            "operation": "Count",
        }
    )
    assert aggregation._apply_date_operation(dt_iso, operation, "UTC") == expected
