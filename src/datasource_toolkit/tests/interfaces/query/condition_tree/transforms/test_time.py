import sys

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from datetime import datetime
from unittest import mock

import freezegun
from forestadmin.datasource_toolkit.interfaces.fields import Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _after_to_greater_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _after_x_hours_to_greater_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _before_to_less_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _before_x_hours_to_less_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _build_interval,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _compare_replacer,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _from_utc_iso_format,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _future_to_greater_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import _get_now  # type: ignore
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _interval_replacer,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    _past_to_less_than,  # type: ignore
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import _start_of  # type: ignore
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    Frequency,
    Interval,
    compare,
    format,
    interval,
    previous_interval,
    previous_interval_to_date,
    time_transforms,
)


@freezegun.freeze_time(datetime(2002, 10, 6, 12, 1, 34))
def test_get_now():
    assert _get_now() == datetime(2002, 10, 6, 12, 1, 34, tzinfo=zoneinfo.ZoneInfo("UTC"))


def test_start_of():
    dt = datetime(2002, 10, 6, 12, 1, 34, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    start_dt = datetime(2002, 10, 6, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert _start_of(dt) == start_dt


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._get_now")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.format")
def test_compare_replacer(mock_format: mock.MagicMock, mock_get_now: mock.MagicMock):
    mock_get_now.return_value = "fake_now"
    mock_format.return_value = "fake_format"

    date_callback = mock.MagicMock()
    date_callback.return_value = datetime(2000, 12, 12, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    compare_replacer = _compare_replacer(Operator.GREATER_THAN, date_callback)

    leaf = ConditionTreeLeaf(field="test", operator=Operator.FUTURE)
    tz = zoneinfo.ZoneInfo("Europe/Paris")
    with mock.patch.object(leaf, "override") as mock_override:
        mock_override.return_value = "fake_override"
        assert compare_replacer(leaf, tz) == "fake_override"
        mock_override.assert_called_once_with({"operator": Operator.GREATER_THAN, "value": "fake_format"})
        mock_format.assert_called_once_with(datetime(2000, 12, 12, tzinfo=tz))
        date_callback.assert_called_once_with("fake_now", leaf.value)


# unable to mock
def test_build_interval():
    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.HOUR.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 12, 22, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.HOUR.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 12, 21, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("UTC")),
        Frequency.HOUR.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 12, 22, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 23, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.HOUR.value,
        periods=4,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 12, 19, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 20, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.DAY.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 12, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.DAY.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 11, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.DAY.value,
        periods=4,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 9, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 10, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.WEEK.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 9, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14), Frequency.WEEK.value, periods=2, tz=zoneinfo.ZoneInfo("Europe/Paris")
    )
    assert res.start == datetime(2002, 12, 2, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 9, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14), Frequency.WEEK.value, periods=4, tz=zoneinfo.ZoneInfo("Europe/Paris")
    )
    assert res.start == datetime(2002, 11, 18, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 11, 25, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.MONTH.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 12, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14), Frequency.MONTH.value, periods=2, tz=zoneinfo.ZoneInfo("Europe/Paris")
    )
    assert res.start == datetime(2002, 11, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.MONTH.value,
        periods=4,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 9, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 10, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.QUARTER.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 10, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.QUARTER.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 7, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 10, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.QUARTER.value,
        periods=4,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 4, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.YEAR.value,
        periods=1,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2002, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.YEAR.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(2001, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2002, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))

    res = _build_interval(
        datetime(2002, 12, 12, 22, 12, 14, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        Frequency.YEAR.value,
        periods=4,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )
    assert res.start == datetime(1999, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert res.end == datetime(2000, 1, 1, 0, 0, 0, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))


@freezegun.freeze_time(datetime(2002, 10, 6, 12, 1, 34))
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._build_interval")
def test_interval_replacer(mock_build_interval: mock.MagicMock):
    mock_build_interval.return_value = Interval(
        start=datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")),
        end=datetime(2001, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")),
    )

    replacer = _interval_replacer(Frequency.YEAR, 2)
    tree = ConditionTreeLeaf(field="test", operator=Operator.PREVIOUS_YEAR)

    res = replacer(tree, zoneinfo.ZoneInfo("UTC"))
    assert res == ConditionTreeBranch(
        Aggregator.AND,
        [
            ConditionTreeLeaf(
                field="test",
                operator=Operator.GREATER_THAN,
                value=datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")).isoformat(timespec="seconds"),
            ),
            ConditionTreeLeaf(
                field="test",
                operator=Operator.LESS_THAN,
                value=datetime(2001, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")).isoformat(timespec="seconds"),
            ),
        ],
    )
    mock_build_interval.assert_called_once_with(
        end=datetime(2002, 10, 6, 12, 1, 34, tzinfo=zoneinfo.ZoneInfo("UTC")),
        frequency=Frequency.YEAR.value,
        periods=2,
        tz=zoneinfo.ZoneInfo("UTC"),
    )

    mock_build_interval.reset_mock()

    tree.value = 15
    replacer = _interval_replacer(Frequency.YEAR, 2, True, datetime(2020, 1, 1))
    res = replacer(tree, zoneinfo.ZoneInfo("Europe/Paris"))
    assert res == ConditionTreeBranch(
        Aggregator.AND,
        [
            ConditionTreeLeaf(
                field="test",
                operator=Operator.GREATER_THAN,
                value=datetime(2000, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")).isoformat(timespec="seconds"),
            ),
            ConditionTreeLeaf(
                field="test",
                operator=Operator.LESS_THAN,
                value=datetime(2001, 1, 1, tzinfo=zoneinfo.ZoneInfo("UTC")).isoformat(timespec="seconds"),
            ),
        ],
    )
    mock_build_interval.assert_called_once_with(
        end=datetime(2020, 1, 1, tzinfo=zoneinfo.ZoneInfo("Europe/Paris")),
        frequency=f"15{Frequency.YEAR.value}",
        periods=2,
        tz=zoneinfo.ZoneInfo("Europe/Paris"),
    )


def test_from_utc_iso_format():
    iso = "2022-05-31T22:00:00.000Z"
    assert _from_utc_iso_format(iso) == datetime(2022, 5, 31, 22, tzinfo=zoneinfo.ZoneInfo("UTC"))

    iso = "2012-11-02T12:12:30.155Z"
    assert _from_utc_iso_format(iso) == datetime(2012, 11, 2, 12, 12, 30, 155000, tzinfo=zoneinfo.ZoneInfo("UTC"))


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._from_utc_iso_format")
def test_before_to_less_than(mock_from_utc_iso_format: mock.MagicMock):
    mock_from_utc_iso_format.return_value = "fake"
    assert _before_to_less_than(datetime(2002, 1, 1), "2022-05-31T22:00:00.000Z") == "fake"
    mock_from_utc_iso_format.assert_called_once_with("2022-05-31T22:00:00.000Z")


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._from_utc_iso_format")
def test_after_to_greater_than(mock_from_utc_iso_format: mock.MagicMock):
    mock_from_utc_iso_format.return_value = "fake"
    assert _after_to_greater_than(datetime(2002, 1, 1), "2022-05-31T22:00:00.000Z") == "fake"
    mock_from_utc_iso_format.assert_called_once_with("2022-05-31T22:00:00.000Z")


def test_past_to_less_than():
    dt = datetime(2003, 1, 1)
    assert _past_to_less_than(dt, "") == dt


def test_future_to_greater_than():
    dt = datetime(2003, 1, 1)
    assert _future_to_greater_than(dt, "") == dt


def test_before_x_hours_to_less_than():
    assert _before_x_hours_to_less_than(datetime(2022, 1, 1, 12), 10) == datetime(2022, 1, 1, 2)


def test_after_x_hours_to_greater_than():
    assert _after_x_hours_to_greater_than(datetime(2022, 1, 1, 12), 10) == datetime(2022, 1, 1, 22)


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._compare_replacer")
def test_compare(mock_compare_replacer: mock.MagicMock):
    mock_compare_replacer.return_value = "fake_replacer"
    date_callback = mock.MagicMock()
    assert compare(Operator.LESS_THAN, date_callback) == {
        "depends_on": [Operator.LESS_THAN],
        "for_types": [PrimitiveType.DATE, PrimitiveType.DATE_ONLY],
        "replacer": "fake_replacer",
    }
    mock_compare_replacer.assert_called_once_with(Operator.LESS_THAN, date_callback)


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._interval_replacer")
def test_interval(mock_intervale_replacer: mock.MagicMock):
    mock_intervale_replacer.return_value = "fake_replacer"

    assert interval(Frequency.DAY, 2, True, datetime(2000, 1, 1)) == {
        "depends_on": [Operator.LESS_THAN, Operator.GREATER_THAN],
        "for_types": [PrimitiveType.DATE, PrimitiveType.DATE_ONLY],
        "replacer": "fake_replacer",
    }
    mock_intervale_replacer.assert_called_once_with(Frequency.DAY, 2, True, datetime(2000, 1, 1))


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.interval")
def test_previous_interval_to_date(mock_interval: mock.MagicMock):
    mock_interval.return_value = "fake_interval"
    assert previous_interval_to_date(Frequency.YEAR, True, datetime(2000, 12, 12), 0) == "fake_interval"
    mock_interval.assert_called_once_with(Frequency.YEAR, 1, True, datetime(2000, 12, 12))

    mock_interval.reset_mock()

    assert previous_interval_to_date(Frequency.YEAR, False, datetime(2000, 12, 12), 12) == "fake_interval"
    mock_interval.assert_called_once_with(Frequency.YEAR, 13, False, datetime(2000, 12, 12))


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.interval")
def test_previous_interval(mock_interval: mock.MagicMock):
    mock_interval.return_value = "fake_interval"
    assert previous_interval(Frequency.YEAR, True, datetime(2000, 12, 12), 0) == "fake_interval"
    mock_interval.assert_called_once_with(Frequency.YEAR, 2, True, datetime(2000, 12, 12))

    mock_interval.reset_mock()

    assert previous_interval(Frequency.YEAR, False, datetime(2000, 12, 12), 12) == "fake_interval"
    mock_interval.assert_called_once_with(Frequency.YEAR, 14, False, datetime(2000, 12, 12))


def test_format():
    dt = datetime(2000, 10, 10, 5, 12, 43, 150, tzinfo=zoneinfo.ZoneInfo("Europe/Paris"))
    assert format(dt) == "2000-10-10T03:12:43+00:00"


@freezegun.freeze_time("2022-01-01")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.compare")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.previous_interval")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time.previous_interval_to_date")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time._start_of")
def test_time_transform(
    mock_start_of: mock.MagicMock,
    mock_previous_interval_to_date: mock.MagicMock,
    mock_previous_interval: mock.MagicMock,
    mock_compare: mock.MagicMock,
):
    mock_compare.side_effect = [
        "fake_before",
        "fake_after",
        "fake_past",
        "fake_future",
        "fake_before_x_hours",
        "fake_after_x_hours",
    ]
    mock_previous_interval.side_effect = [
        "fake_previous_year",
        "fake_previous_quarter",
        "fake_previous_month",
        "fake_previous_week",
        "fake_yesterday",
        "fake_previous_x_days",
        "fake_today",
    ]
    mock_previous_interval_to_date.side_effect = [
        "fake_previous_year_to_date",
        "fake_previous_quarter_to_date",
        "fake_previous_month_to_date",
        "fake_previous_week_to_date",
        "fake_previous_x_days_to_date",
    ]
    mock_start_of.return_value = "fake_start_of"

    assert time_transforms(12) == {
        Operator.BEFORE: ["fake_before"],
        Operator.AFTER: ["fake_after"],
        Operator.PAST: ["fake_past"],
        Operator.FUTURE: ["fake_future"],
        Operator.BEFORE_X_HOURS_AGO: ["fake_before_x_hours"],
        Operator.AFTER_X_HOURS_AGO: ["fake_after_x_hours"],
        Operator.PREVIOUS_YEAR: ["fake_previous_year"],
        Operator.PREVIOUS_MONTH: ["fake_previous_month"],
        Operator.PREVIOUS_QUARTER: ["fake_previous_quarter"],
        Operator.PREVIOUS_WEEK: ["fake_previous_week"],
        Operator.YESTERDAY: ["fake_yesterday"],
        Operator.PREVIOUS_X_DAYS: ["fake_previous_x_days"],
        Operator.TODAY: ["fake_today"],
        Operator.PREVIOUS_YEAR_TO_DATE: ["fake_previous_year_to_date"],
        Operator.PREVIOUS_QUARTER_TO_DATE: ["fake_previous_quarter_to_date"],
        Operator.PREVIOUS_MONTH_TO_DATE: ["fake_previous_month_to_date"],
        Operator.PREVIOUS_WEEK_TO_DATE: ["fake_previous_week_to_date"],
        Operator.PREVIOUS_X_DAYS_TO_DATE: ["fake_previous_x_days_to_date"],
    }
    mock_start_of.assert_called_once_with(datetime(2022, 1, 2, tzinfo=zoneinfo.ZoneInfo(key="UTC")))
    mock_compare.assert_has_calls(
        [
            mock.call(Operator.LESS_THAN, _before_to_less_than),
            mock.call(Operator.GREATER_THAN, _after_to_greater_than),
            mock.call(Operator.LESS_THAN, _past_to_less_than),
            mock.call(Operator.GREATER_THAN, _future_to_greater_than),
            mock.call(Operator.LESS_THAN, _before_x_hours_to_less_than),
            mock.call(Operator.GREATER_THAN, _after_x_hours_to_greater_than),
        ]
    )

    mock_previous_interval.assert_has_calls(
        [
            mock.call(Frequency.YEAR, shift=12),
            mock.call(Frequency.QUARTER, shift=12),
            mock.call(Frequency.MONTH, shift=12),
            mock.call(Frequency.WEEK, shift=12),
            mock.call(Frequency.DAY, shift=12),
            mock.call(Frequency.DAY, True, shift=12),
            mock.call(Frequency.DAY, end="fake_start_of", shift=12),
        ]
    )
    mock_previous_interval_to_date.assert_has_calls(
        [
            mock.call(Frequency.YEAR, shift=12),
            mock.call(Frequency.QUARTER, shift=12),
            mock.call(Frequency.MONTH, shift=12),
            mock.call(Frequency.WEEK, shift=12),
            mock.call(Frequency.DAY, True, shift=12),
        ]
    )
