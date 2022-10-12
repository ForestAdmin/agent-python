from typing import List
from unittest import mock

import pytest
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort, SortException
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def test_sort_projection():
    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])
    assert sort.projection == Projection("c1", "c2")


def test_sort_replace_clauses():
    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])
    replace_cb = mock.MagicMock()
    replace_cb.side_effect = [{"field": "r1:c1", "ascending": False}, [{"field": "r1:c2", "ascending": False}]]
    assert sort.replace_clauses(replace_cb) == Sort(
        [{"field": "r1:c1", "ascending": False}, {"field": "r1:c2", "ascending": False}]
    )


def test_sort_nest():
    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])
    assert sort.nest("r1") == Sort([{"field": "r1:c1", "ascending": False}, {"field": "r1:c2", "ascending": True}])


def test_sort_inverse():
    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])
    assert sort.inverse() == Sort([{"field": "c1", "ascending": True}, {"field": "c2", "ascending": False}])


def test_sort_unnest():
    sort = Sort([{"field": "r1:c1", "ascending": False}, {"field": "r1:c2", "ascending": True}])
    assert sort.unnest() == Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])

    sort = Sort([{"field": "r1:c1", "ascending": False}, {"field": "c2", "ascending": True}])
    with pytest.raises(SortException):
        sort.unnest()


def test_apply():

    records: List[RecordsDataAlias] = [
        {
            "c1": "a",
            "c2": "b",
            "c3": "c",
        },
        {
            "c1": "b",
            "c2": "a",
            "c3": "d",
        },
        {"c1": "a", "c2": "a", "c3": "c"},
    ]

    sort = Sort([{"field": "c1", "ascending": True}])
    assert sort.apply(records) == [
        {
            "c1": "a",
            "c2": "b",
            "c3": "c",
        },
        {"c1": "a", "c2": "a", "c3": "c"},
        {
            "c1": "b",
            "c2": "a",
            "c3": "d",
        },
    ]

    sort = Sort([{"field": "c1", "ascending": True}, {"field": "c2", "ascending": True}])
    assert sort.apply(records) == [
        {"c1": "a", "c2": "a", "c3": "c"},
        {
            "c1": "a",
            "c2": "b",
            "c3": "c",
        },
        {
            "c1": "b",
            "c2": "a",
            "c3": "d",
        },
    ]

    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": True}])
    assert sort.apply(records) == [
        {
            "c1": "b",
            "c2": "a",
            "c3": "d",
        },
        {"c1": "a", "c2": "a", "c3": "c"},
        {
            "c1": "a",
            "c2": "b",
            "c3": "c",
        },
    ]

    sort = Sort([{"field": "c1", "ascending": False}, {"field": "c2", "ascending": False}])
    assert sort.apply(records) == [
        {
            "c1": "b",
            "c2": "a",
            "c3": "d",
        },
        {
            "c1": "a",
            "c2": "b",
            "c3": "c",
        },
        {"c1": "a", "c2": "a", "c3": "c"},
    ]
