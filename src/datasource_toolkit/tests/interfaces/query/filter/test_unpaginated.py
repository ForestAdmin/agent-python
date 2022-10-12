from unittest import mock

import pytest
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter, FilterComponent


def test_filter_constructor():
    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="UTC",
    )
    f = Filter(component)
    assert f.condition_tree == component.get("condition_tree")
    assert f.search == component.get("search")
    assert f.search_extended == component.get("search_extended")
    assert f.segment == component.get("segment")
    assert f.timezone == component.get("timezone")


def test_filter_eq():
    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="UTC",
    )
    f = Filter(component)
    f2 = Filter(component)

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


def test_is_nestable():
    component = FilterComponent(timezone="UTC")
    f = Filter(component)
    assert f.is_nestable

    f.search = "a"
    assert f.is_nestable is False

    f.search = None
    f.segment = "test"

    assert f.is_nestable is False

    f.search = "a"
    assert f.is_nestable is False


def test_to_filter_component():

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
        timezone="UTC",
    )
    f = Filter(component)

    assert f.to_filter_component() == component

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
        segment="test_segment",
    )
    f = Filter(component)

    assert f.to_filter_component() == component

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
        search_extended=True,
    )
    f = Filter(component)

    assert f.to_filter_component() == component

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
    )
    f = Filter(component)

    assert f.to_filter_component() == component

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
    )
    f = Filter(component)

    assert f.to_filter_component() == component


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated.Filter.to_filter_component")
def test_override_component(mock_to_component: mock.MagicMock):
    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
    )
    f = Filter(component)
    fake_component = mock.MagicMock(name="mock_compoent")
    mock_to_component.return_value = fake_component
    fake_component.update = mock.MagicMock()
    res = f.override_component({"timezone": "UTC"})
    assert res == fake_component
    mock_to_component.assert_called_once()
    fake_component.update.assert_called_once_with({"timezone": "UTC"})  # type: ignore


def test_override():

    component = FilterComponent(
        condition_tree=ConditionTreeLeaf(field="test", operator=Operator.BLANK),
        search="test",
    )
    f = Filter(component)
    with mock.patch.object(f, "override_component") as mock_override_component:
        mock_override_component.return_value = {}
        res = f.override({"timezone": "UTC"})
        mock_override_component.assert_called_once_with({"timezone": "UTC"})
        assert res == Filter({})


def test_nest_arguments():
    component = FilterComponent(
        search="test",
    )
    f = Filter(component)
    assert f._nest_arguments("test") == {}  # type: ignore

    f.condition_tree = ConditionTreeLeaf("test", Operator.BLANK)
    with mock.patch.object(f.condition_tree, "nest") as mock_nest:
        mock_nest.return_value = "fake_condition_tree"
        assert f._nest_arguments("prefix") == {"condition_tree": "fake_condition_tree"}  # type: ignore
        mock_nest.assert_called_once_with("prefix")


def test_nest():
    component = FilterComponent(
        search="test",
    )
    with mock.patch.multiple(
        "forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated.Filter",
        override=mock.DEFAULT,
        _nest_arguments=mock.DEFAULT,
    ) as mocks:
        with mock.patch(
            "forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated.Filter.is_nestable",
            new_callable=mock.PropertyMock,
        ) as mock_is_nestable:
            mock_is_nestable.return_value = False
            f = Filter(component)
            with pytest.raises(DatasourceToolkitException):
                f.nest("prefix")

            mock_is_nestable.return_value = True

            mocks["override"].return_value = "fake_override"
            mocks["_nest_arguments"].return_value = "fake_arguments"
            assert f.nest("prefix") == "fake_override"
            mocks["override"].assert_called_once_with("fake_arguments")

            mocks["override"].side_effect = [DatasourceToolkitException]
            assert f.nest("prefix") == f
