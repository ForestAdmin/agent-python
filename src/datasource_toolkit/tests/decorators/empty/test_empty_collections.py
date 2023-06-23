import asyncio
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

if sys.version_info >= (3, 8):
    from unittest.mock import AsyncMock
else:
    from mock import AsyncMock

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.decorators.datasource_decorator import DatasourceDecorator
from forestadmin.datasource_toolkit.decorators.empty.collection import EmptyCollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import Operator
from forestadmin.datasource_toolkit.interfaces.query.aggregation import Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import Aggregator, ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter, PaginatedFilterComponent
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection


class TestEmptyCollectionDecorator(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.datasource: Datasource = Datasource()
        cls.datasource.get_collection = lambda x: cls.datasource._collections[x]
        cls.mocked_caller = User(
            rendering_id=1,
            user_id=1,
            tags={},
            email="dummy@user.fr",
            first_name="dummy",
            last_name="user",
            team="operational",
            timezone=zoneinfo.ZoneInfo("Europe/Paris"),
        )

        cls.collection_order: Collection = Mock(Collection)
        cls.collection_order.name = "order"
        cls.collection_order.list = AsyncMock(return_value=[{"id": 3, "cost": 22}])
        cls.collection_order.update = AsyncMock(return_value=None)
        cls.collection_order.delete = AsyncMock(return_value=None)
        cls.collection_order.aggregate = AsyncMock(return_value=[{"value": 1, "group": {}}])

        cls.datasource.add_collection(cls.collection_order)

        cls.datasource_decorator = DatasourceDecorator(cls.datasource, EmptyCollectionDecorator)
        cls.decorated_collection = cls.datasource_decorator.get_collection("order")

        cls.empty_paginated_filter: PaginatedFilter = PaginatedFilter(
            PaginatedFilterComponent(
                condition_tree=ConditionTreeBranch(
                    aggregator=Aggregator.AND,
                    conditions=[
                        ConditionTreeLeaf("cost", Operator.EQUAL, 25),
                        ConditionTreeLeaf("cost", Operator.EQUAL, 20),
                        ConditionTreeLeaf("id", Operator.IN, [12, 23]),
                        ConditionTreeLeaf("id", Operator.IN, [34, 45]),
                    ],
                )
            )
        )
        cls.not_empty_paginated_filter: PaginatedFilter = PaginatedFilter(
            PaginatedFilterComponent(
                condition_tree=ConditionTreeBranch(
                    aggregator=Aggregator.AND,
                    conditions=[
                        ConditionTreeLeaf("cost", Operator.EQUAL, 22),
                        ConditionTreeLeaf("cost", Operator.EQUAL, 22),
                        ConditionTreeLeaf("id", Operator.IN, [1, 2, 2, 3]),
                        ConditionTreeLeaf("id", Operator.IN, [3, 4, 4, 5]),
                    ],
                )
            )
        )

    def test_schema_not_changed(self):
        assert self.decorated_collection.schema == self.collection_order.schema

    def test_list(self):
        # empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=True):
            result = self.loop.run_until_complete(
                self.decorated_collection.list(
                    self.mocked_caller, self.empty_paginated_filter, Projection("id", "cost")
                )
            )
            assert len(result) == 0
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.list.assert_not_awaited()

        # not empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=False):
            result = self.loop.run_until_complete(
                self.decorated_collection.list(
                    self.mocked_caller, self.not_empty_paginated_filter, Projection("id", "cost")
                )
            )
            assert len(result) == 1
            assert result[0] == {"id": 3, "cost": 22}
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.list.assert_awaited()
            self.collection_order.list.reset_mock()

        # empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.list(self.mocked_caller, self.empty_paginated_filter, Projection("id", "cost"))
        )
        assert len(result) == 0
        self.collection_order.list.assert_not_awaited()

        # not empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.list(
                self.mocked_caller, self.not_empty_paginated_filter, Projection("id", "cost")
            )
        )
        assert len(result) == 1
        assert result[0] == {"id": 3, "cost": 22}
        self.collection_order.list.assert_awaited()
        self.collection_order.list.reset_mock()

    def test_update(self):
        # empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=True):
            result = self.loop.run_until_complete(
                self.decorated_collection.update(self.mocked_caller, self.empty_paginated_filter, {"id": 3, "cost": 12})
            )
            assert result is None
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.update.assert_not_awaited()

        # not empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=False):
            result = self.loop.run_until_complete(
                self.decorated_collection.update(
                    self.mocked_caller, self.not_empty_paginated_filter, {"id": 3, "cost": 12}
                )
            )
            assert result is None
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.update.assert_awaited()
            self.collection_order.update.reset_mock()

        # empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.update(self.mocked_caller, self.empty_paginated_filter, {"id": 3, "cost": 12})
        )
        assert result is None
        self.collection_order.update.assert_not_awaited()

        # not empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.update(self.mocked_caller, self.not_empty_paginated_filter, {"id": 3, "cost": 12})
        )
        assert result is None
        self.collection_order.update.assert_awaited()
        self.collection_order.update.reset_mock()

    def test_delete(self):
        # empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=True):
            result = self.loop.run_until_complete(
                self.decorated_collection.delete(self.mocked_caller, self.empty_paginated_filter)
            )
            assert result is None
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.delete.assert_not_awaited()

        # not empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=False):
            result = self.loop.run_until_complete(
                self.decorated_collection.delete(self.mocked_caller, self.not_empty_paginated_filter)
            )
            assert result is None
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.delete.assert_awaited()
            self.collection_order.delete.reset_mock()

        # empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.delete(self.mocked_caller, self.empty_paginated_filter)
        )
        assert result is None
        self.collection_order.delete.assert_not_awaited()

        # not empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.delete(self.mocked_caller, self.not_empty_paginated_filter)
        )
        assert result is None
        self.collection_order.delete.assert_awaited()
        self.collection_order.delete.reset_mock()

    def test_aggregate(self):
        # empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=True):
            result = self.loop.run_until_complete(
                self.decorated_collection.aggregate(
                    self.mocked_caller,
                    self.empty_paginated_filter,
                    Aggregation({"field": None, "operation": "Count", "groups": []}),
                )
            )
            assert len(result) == 0
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.aggregate.assert_not_awaited()
        # not empty filter
        with patch.object(self.decorated_collection, "_returns_empty_set", return_value=False):
            result = self.loop.run_until_complete(
                self.decorated_collection.aggregate(
                    self.mocked_caller,
                    self.not_empty_paginated_filter,
                    Aggregation({"field": None, "operation": "Count", "groups": []}),
                )
            )
            assert len(result) == 1
            assert result[0] == {"value": 1, "group": {}}
            self.decorated_collection._returns_empty_set.assert_called_once()
            self.decorated_collection._returns_empty_set.reset_mock()
            self.collection_order.aggregate.assert_awaited()
            self.collection_order.aggregate.reset_mock()

        # empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.aggregate(
                self.mocked_caller,
                self.empty_paginated_filter,
                Aggregation({"field": None, "operation": "Count", "groups": []}),
            )
        )
        assert len(result) == 0
        self.collection_order.aggregate.assert_not_awaited()

        # not empty filter
        result = self.loop.run_until_complete(
            self.decorated_collection.aggregate(
                self.mocked_caller,
                self.not_empty_paginated_filter,
                Aggregation({"field": None, "operation": "Count", "groups": []}),
            )
        )
        assert len(result) == 1
        assert result[0] == {"value": 1, "group": {}}
        self.collection_order.aggregate.assert_awaited()
        self.collection_order.aggregate.reset_mock()

    def test_returns_empty_set(self):
        # in []
        condition_tree: ConditionTree = ConditionTreeLeaf("id", Operator.IN, [])
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is True

        # no conditions
        condition_tree: ConditionTree = ConditionTreeBranch(Aggregator.OR, conditions=[])
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is True

        # and with empty condition
        condition_tree: ConditionTree = ConditionTreeBranch(
            Aggregator.AND,
            conditions=[ConditionTreeLeaf("id", Operator.IN, []), ConditionTreeLeaf("id", Operator.IN, [])],
        )
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is True

        # or with empty condition
        condition_tree: ConditionTree = ConditionTreeBranch(
            Aggregator.OR,
            conditions=[ConditionTreeLeaf("id", Operator.IN, []), ConditionTreeLeaf("id", Operator.IN, [])],
        )
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is True

        # complex returning empty set
        condition_tree: ConditionTree = ConditionTreeBranch(
            aggregator=Aggregator.OR,
            conditions=[
                ConditionTreeBranch(
                    aggregator=Aggregator.AND,
                    conditions=[
                        ConditionTreeLeaf("cost", Operator.EQUAL, 25),
                        ConditionTreeLeaf("cost", Operator.EQUAL, 20),
                    ],
                ),
                ConditionTreeBranch(
                    aggregator=Aggregator.AND,
                    conditions=[
                        ConditionTreeLeaf("id", Operator.IN, [12, 23]),
                        ConditionTreeLeaf("id", Operator.IN, [34, 45]),
                    ],
                ),
            ],
        )
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is True

        # complex returning not empty set
        condition_tree: ConditionTree = ConditionTreeBranch(
            aggregator=Aggregator.AND,
            conditions=[
                ConditionTreeBranch(
                    aggregator=Aggregator.OR,
                    conditions=[
                        ConditionTreeLeaf("cost", Operator.EQUAL, 25),
                        ConditionTreeLeaf("cost", Operator.EQUAL, 20),
                    ],
                ),
                ConditionTreeBranch(
                    aggregator=Aggregator.OR,
                    conditions=[
                        ConditionTreeLeaf("id", Operator.IN, [12, 23]),
                        ConditionTreeLeaf("id", Operator.IN, [34, 45]),
                    ],
                ),
            ],
        )
        ret = self.decorated_collection._returns_empty_set(condition_tree)
        assert ret is False

    def test_returns_empty_set_bad_parameter(self):
        ret = self.decorated_collection._returns_empty_set(None)
        assert ret is False
