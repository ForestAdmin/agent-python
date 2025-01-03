import sys
from typing import cast
from unittest import mock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import pytest
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, ManyToMany, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.factory import FilterFactory, FilterFactoryException
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection

mocked_caller = User(
    rendering_id=1,
    user_id=1,
    tags={},
    email="dummy@user.fr",
    first_name="dummy",
    last_name="user",
    team="operational",
    timezone=zoneinfo.ZoneInfo("Europe/Paris"),
    request={"ip": "127.0.0.1"},
)


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.filter.factory.time_transforms")
def test_shift_period_filter(mock_time_transform: mock.MagicMock):
    shift_period_filter_replacer = FilterFactory._shift_period_filter("UTC")  # type: ignore
    leaf = ConditionTreeLeaf(field="test", operator=Operator.PREVIOUS_YEAR)
    mock_replacer = mock.MagicMock(return_value="fake_replacer")
    mock_time_transform.return_value = {Operator.PREVIOUS_YEAR: [{"replacer": mock_replacer}]}
    with mock.patch(
        "forestadmin.datasource_toolkit.interfaces.query.filter.factory.SHIFTED_OPERATORS", {Operator.PREVIOUS_YEAR}
    ):
        assert shift_period_filter_replacer(leaf) == "fake_replacer"
        mock_time_transform.assert_called_once_with(1)
        mock_replacer.assert_called_once_with(leaf, "UTC")

    with mock.patch("forestadmin.datasource_toolkit.interfaces.query.filter.factory.SHIFTED_OPERATORS", {}):
        with pytest.raises(FilterFactoryException):
            shift_period_filter_replacer(leaf)


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.filter.factory.FilterFactory._shift_period_filter")
def test_get_previous_period_filter(mock_shifted_period: mock.MagicMock):
    leaf = ConditionTreeLeaf(field="test", operator=Operator.PREVIOUS_MONTH)
    filter = Filter({"condition_tree": leaf, "timezone": zoneinfo.ZoneInfo("Europe/Paris")})
    with mock.patch.object(filter, "override") as override_mock:
        with mock.patch.object(leaf, "replace") as replace_override:
            override_mock.return_value = "fake_override"
            mock_shifted_period.return_value = "fake_shift_period"
            replace_override.return_value = "fake_replace"
            assert FilterFactory.get_previous_period_filter(filter) == "fake_override"
            override_mock.assert_called_once_with({"condition_tree": "fake_replace"})
            replace_override.assert_called_once_with("fake_shift_period")
            mock_shifted_period.assert_called_once_with(filter.timezone)

    filter = Filter({"timezone": zoneinfo.ZoneInfo("UTC")})
    with pytest.raises(FilterFactoryException):
        FilterFactory.get_previous_period_filter(filter)


@pytest.mark.asyncio
async def test_make_through_filter():
    with mock.patch(
        "forestadmin.datasource_toolkit.interfaces.query.filter.factory.CollectionUtils.get_value",
        new_callable=mock.AsyncMock,
    ) as mock_get_value:
        with mock.patch(
            "forestadmin.datasource_toolkit.interfaces.query.filter.factory.FilterFactory.make_foreign_filter",
            new_callable=mock.AsyncMock,
        ) as mock_make_foreign_filter:
            with mock.patch.object(Collection, "__abstractmethods__", new_callable=set):
                collection = Collection(name="test", datasource=mock.MagicMock())  # type: ignore
                collection.schema["fields"] = {
                    "fake_relation": {
                        "type": FieldType.MANY_TO_ONE,
                        "foreign_collection": "fake",
                        "foreign_key": "test_id",
                        "foreign_key_target": "id",
                    }
                }

                # test with nestable PaginatedFilter
                mock_get_value.return_value = "fake_value"
                collection.schema["fields"] = {
                    "parent": {
                        "type": FieldType.MANY_TO_MANY,
                        "through_collection": "association",
                        "foreign_collection": "parent",
                        "foreign_key": "parent_id",
                        "foreign_key_target": "id",
                        "origin_key": "child_id",
                        "origin_key_target": "id",
                        "foreign_relation": "parent",
                    }
                }

                mock_collection = mock.MagicMock()
                mock_collection.list = mock.AsyncMock(return_value=[{"id": 1}])
                with mock.patch.object(collection.datasource, "get_collection", return_value=mock_collection):
                    res = await FilterFactory.make_through_filter(
                        mocked_caller,
                        collection,
                        [1],
                        "parent",
                        PaginatedFilter(
                            {
                                "timezone": zoneinfo.ZoneInfo("UTC"),
                            }
                        ),
                    )

                assert res.condition_tree.aggregator == Aggregator.AND
                assert ConditionTreeLeaf("child_id", Operator.EQUAL, "fake_value") in res.condition_tree.conditions
                assert ConditionTreeLeaf("parent_id", Operator.IN, [1]) in res.condition_tree.conditions

                mock_get_value.assert_called_once_with(mocked_caller, collection, [1], "id")
                mock_get_value.reset_mock()

                # test with unnestable PaginatedFilter
                fake_collection = mock.Mock(name="fake_collection", spec=Collection)
                fake_collection.list = mock.AsyncMock(
                    return_value=[
                        {"id": "fake_record_1"},
                        {"id": "fake_record_2"},
                    ]
                )

                fake_datasource = mock.MagicMock()
                fake_datasource.get_collection = mock.MagicMock(return_value=fake_collection)
                collection._datasource = fake_datasource  # type: ignore

                mock_make_foreign_filter.reset_mock()
                mock_make_foreign_filter.return_value = "fake_filter"
                mock_get_value.return_value = "fake_value"

                with mock.patch(
                    "forestadmin.datasource_toolkit.interfaces.query.filter.factory.CollectionUtils.get_through_target",
                    return_value="association",
                ):
                    res = await FilterFactory.make_through_filter(
                        mocked_caller,
                        collection,
                        [1],
                        "parent",
                        PaginatedFilter(
                            {
                                "search": "a",
                                "timezone": zoneinfo.ZoneInfo("UTC"),
                            }
                        ),
                    )
                mock_get_value.assert_called_once_with(mocked_caller, collection, [1], "id")
                fake_datasource.get_collection.assert_called_once_with("parent")  # type: ignore
                mock_make_foreign_filter.assert_called_once_with(
                    mocked_caller,
                    collection,
                    [1],
                    cast(ManyToMany, collection.schema["fields"]["parent"]),
                    PaginatedFilter(
                        {
                            "search": "a",
                            "timezone": zoneinfo.ZoneInfo("UTC"),
                        }
                    ),
                )
                fake_collection.list.assert_called_once_with(
                    mocked_caller, "fake_filter", Projection("id")
                )  # type: ignore
                assert res == PaginatedFilter(
                    {
                        "condition_tree": ConditionTreeBranch(
                            Aggregator.AND,
                            conditions=[
                                ConditionTreeLeaf("child_id", Operator.EQUAL, "fake_value"),
                                ConditionTreeLeaf("parent_id", Operator.IN, ["fake_record_1", "fake_record_2"]),
                            ],
                        )
                    }
                )
