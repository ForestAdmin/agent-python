from unittest import mock

from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter, PaginatedFilterComponent
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter, FilterComponent
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort


def test_filter_constructor():
    component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="utc",
        page=Page(),
        sort=Sort(),
    )
    f = PaginatedFilter(component)
    assert f.condition_tree == component.get("condition_tree")
    assert f.search == component.get("search")
    assert f.search_extended == component.get("search_extended")
    assert f.segment == component.get("segment")
    assert f.timezone == component.get("timezone")
    assert f.page == component.get("page")
    assert f.sort == component.get("sort")


def test_filter_eq():
    component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="utc",
        page=Page(limit=1),
        sort=Sort([{"field": "test", "ascending": True}]),
    )
    f = PaginatedFilter(component)
    f2 = PaginatedFilter(component)

    assert f == f2

    f2.condition_tree = ConditionTreeLeaf(field="test", operator=Operator.FUTURE)

    assert f != f2

    f.condition_tree = f2.condition_tree
    f2.search = "other"
    assert f != f2

    f2.search = f.search
    f2.search_extended = False
    assert f != f2

    f2.search_extended = f.search_extended
    f.segment = "other"
    assert f2 != f

    f2.segment = f.segment
    f2.timezone = "europe/Paris"

    assert f != f2

    f2.timezone = f.timezone
    f2.page = Page(limit=2)

    assert f != f2

    f2.page = f.page
    f2.sort = Sort([{"field": "test", "ascending": False}])

    assert f2 != f


def test_from_base_filter():
    component = FilterComponent(
        condition_tree=ConditionTreeLeaf("test", Operator.BLANK),
        search="search_test",
        search_extended=True,
        segment="fake_segment",
        timezone="fake_timezone",
    )
    f = Filter(component)

    assert PaginatedFilter.from_base_filter(f) == PaginatedFilter(
        PaginatedFilterComponent(
            condition_tree=ConditionTreeLeaf("test", Operator.BLANK),
            search="search_test",
            search_extended=True,
            segment="fake_segment",
            timezone="fake_timezone",
        )
    )


def test_to_base_filter():

    filter_component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="utc",
        page=Page(),
        sort=Sort(),
    )
    f = PaginatedFilter(filter_component)
    assert f.to_base_filter() == Filter(
        FilterComponent(
            condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
            search="test",
            search_extended=True,
            segment="test_segment",
            timezone="utc",
        )
    )


def test_to_filter_component():
    filter_component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="utc",
        page=Page(),
        sort=Sort([{"field": "test", "ascending": False}]),
    )
    f = PaginatedFilter(filter_component)

    assert f.to_filter_component() == filter_component


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.filter.paginated.BaseFilter._nest_arguments")
def test_nest_arguments(mock_nest_arguments: mock.MagicMock):
    filter_component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
    )
    f = PaginatedFilter(filter_component)

    mock_nest_arguments.return_value = {"fake": "args"}
    res = f._nest_arguments("prefix")  # type: ignore
    assert res == {"fake": "args"}
    mock_nest_arguments.assert_called_once_with("prefix")

    mock_nest_arguments.reset_mock()
    filter_component = PaginatedFilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        sort=Sort([{"field": "test", "ascending": False}]),
    )
    f = PaginatedFilter(filter_component)
    with mock.patch.object(f.sort, "nest") as mock_sort_nest:

        mock_nest_arguments.return_value = {"fake": "args"}
        mock_sort_nest.return_value = "fake"
        res = f._nest_arguments("prefix")  # type: ignore
        assert res == {"fake": "args", "sort": "fake"}
        mock_sort_nest.assert_called_once_with("prefix")
        mock_nest_arguments.assert_called_once_with("prefix")
