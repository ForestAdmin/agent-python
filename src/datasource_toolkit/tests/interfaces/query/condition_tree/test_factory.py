# pyright: reportPrivateUsage=false
from typing import List
from unittest import mock

import pytest
from forestadmin.datasource_toolkit.interfaces.fields import Column, FieldType, Operator, PrimitiveType
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
    ConditionTreeFactoryException,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator,
    BranchComponents,
    ConditionTreeBranch,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf, LeafComponents

PRIMARY_KEY_FIELD: Column = {
    "column_type": PrimitiveType.NUMBER,
    "filter_operators": None,
    "default_value": None,
    "enum_values": None,
    "is_primary_key": True,
    "is_read_only": True,
    "is_sortable": True,
    "validations": None,
    "type": FieldType.COLUMN,
}


@mock.patch.object(ConditionTreeFactory, "match_ids")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.RecordUtils.get_primary_key")
def test_match_records(get_primary_key_mock: mock.Mock, match_ids_mock: mock.Mock):
    pks = [1, 2]
    get_primary_key_mock.side_effect = pks
    match_ids_mock.return_value = "result"

    schema: CollectionSchema = {
        "actions": {},
        "fields": {"id": PRIMARY_KEY_FIELD},
        "searchable": False,
        "segments": [],
    }
    records = [{"id": 1}, {"id": 2}]

    assert ConditionTreeFactory.match_records(schema, records) == "result"
    get_primary_key_mock.assert_has_calls([mock.call(schema, records[0]), mock.call(schema, records[1])])
    match_ids_mock.assert_called_once_with(schema, [1, 2])


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.SchemaUtils.get_primary_keys")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.ConditionTreeFactory._match_fields")
def test_match_ids(match_field_mock: mock.Mock, get_pk_mock: mock.Mock):
    PRIMARY_KEY_FIELD["is_primary_key"] = False
    schema: CollectionSchema = {
        "actions": {},
        "fields": {"id": PRIMARY_KEY_FIELD},
        "searchable": False,
        "segments": [],
    }
    get_pk_mock.return_value = []
    with pytest.raises(ConditionTreeFactoryException) as e:
        ConditionTreeFactory.match_ids(schema, [[1]])

    assert str(e.value) == "🌳🌳🌳Collection must have at least one primary key"

    PRIMARY_KEY_FIELD["is_primary_key"] = True
    schema: CollectionSchema = {
        "actions": {},
        "fields": {"id": PRIMARY_KEY_FIELD},
        "searchable": False,
        "segments": [],
    }
    get_pk_mock.return_value = ["id"]

    with pytest.raises(ConditionTreeFactoryException) as e:
        ConditionTreeFactory.match_ids(schema, [[1]])

    assert str(e.value) == "🌳🌳🌳Field id must support opperators: [equal, in]"

    PRIMARY_KEY_FIELD["is_primary_key"] = True
    PRIMARY_KEY_FIELD["filter_operators"] = {Operator.IN}
    schema: CollectionSchema = {
        "actions": {},
        "fields": {"id": PRIMARY_KEY_FIELD},
        "searchable": False,
        "segments": [],
    }
    get_pk_mock.return_value = ["id"]
    match_field_mock.return_value = "result"
    assert ConditionTreeFactory.match_ids(schema, [[1]]) == "result"
    match_field_mock.assert_called_once_with(["id"], [[1]])


@mock.patch.object(ConditionTreeFactory, "_group")
def test_union(group_mock: mock.Mock):
    trees: List[ConditionTree] = [
        ConditionTreeLeaf(field="id", operator=Operator.BLANK),
        ConditionTreeLeaf(field="id", operator=Operator.MISSING),
    ]
    group_mock.return_value = "result"
    assert ConditionTreeFactory.union(trees) == "result"
    group_mock.assert_called_once_with(Aggregator.OR, trees)


@mock.patch.object(ConditionTreeFactory, "_group")
def test_intersect(group_mock: mock.Mock):
    trees: List[ConditionTree] = [
        ConditionTreeLeaf(field="id", operator=Operator.BLANK),
        ConditionTreeLeaf(field="id", operator=Operator.MISSING),
    ]
    tree = ConditionTreeBranch(Aggregator.AND, [])
    group_mock.return_value = tree
    with pytest.raises(ConditionTreeFactoryException) as e:
        ConditionTreeFactory.intersect(trees)
    assert str(e.value) == "🌳🌳🌳Empty intersect"

    tree = ConditionTreeBranch(Aggregator.AND, trees)
    group_mock.return_value = tree
    assert ConditionTreeFactory.intersect(trees) == tree


@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.is_leaf_component")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.is_branch_component")
@mock.patch("forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.ConditionTreeLeaf.load")
@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree"
    ".factory.ConditionTreeFactory._from_branch_plain_object"
)
def test_from_plain_object(
    from_branch_plain_object_mock: mock.Mock,
    leaf_load_mock: mock.Mock,
    is_branch_components_mock: mock.Mock,
    is_leaf_components_mock: mock.Mock,
):
    leaf_component: LeafComponents = {"field": "id", "operator": "in", "value": [1, 2]}
    is_leaf_components_mock.return_value = True
    leaf_load_mock.return_value = ConditionTreeLeaf("id", Operator.IN, [1, 2])

    assert ConditionTreeFactory.from_plain_object(leaf_component) == ConditionTreeLeaf("id", Operator.IN, [1, 2])
    is_leaf_components_mock.assert_called_once_with(leaf_component)
    leaf_load_mock.assert_called_once_with(leaf_component)
    is_branch_components_mock.assert_not_called()
    from_branch_plain_object_mock.assert_not_called()

    is_leaf_components_mock.reset_mock()
    leaf_load_mock.reset_mock()
    is_leaf_components_mock.return_value = False
    is_branch_components_mock.return_value = True

    branch = ConditionTreeBranch(Aggregator.OR, [ConditionTreeLeaf("id", Operator.IN, [1, 2])])
    from_branch_plain_object_mock.return_value = branch

    branch_component: BranchComponents = {
        "aggregator": "or",
        "conditions": [leaf_component],
    }
    assert ConditionTreeFactory.from_plain_object(branch_component) == branch
    is_leaf_components_mock.assert_called_once_with(branch_component)
    is_branch_components_mock.assert_called_once_with(branch_component)
    from_branch_plain_object_mock.assert_called_once_with(branch_component)
    leaf_load_mock.assert_not_called()

    is_leaf_components_mock.reset_mock()
    is_branch_components_mock.reset_mock()
    from_branch_plain_object_mock.reset_mock()
    leaf_load_mock.reset_mock()

    is_leaf_components_mock.return_value = False
    is_branch_components_mock.return_value = False
    with pytest.raises(ConditionTreeFactoryException) as e:
        ConditionTreeFactory.from_plain_object({})
    assert str(e.value) == "🌳🌳🌳Failed to instantiate condition tree from json"
    is_leaf_components_mock.assert_called_once_with({})
    is_branch_components_mock.assert_called_once_with({})
    from_branch_plain_object_mock.assert_not_called()
    leaf_load_mock.assert_not_called()


# Use mock is hard with recursive method
def test_match_fields():
    fields = ["id"]
    values = []

    assert ConditionTreeFactory._match_fields(fields, values) == ConditionTreeFactory.MATCH_NONE

    values = [[1]]
    assert ConditionTreeFactory._match_fields(fields, values) == ConditionTreeLeaf("id", Operator.EQUAL, 1)

    values = [[1], [2]]
    assert ConditionTreeFactory._match_fields(fields, values) == ConditionTreeLeaf("id", Operator.IN, [1, 2])

    fields = ["id", "stock"]
    values = [[1, 12], [2]]
    res = ConditionTreeFactory._match_fields(fields, values)
    assert res == ConditionTreeFactory.union(
        [
            ConditionTreeBranch(
                aggregator=Aggregator.OR,
                conditions=[
                    ConditionTreeBranch(
                        aggregator=Aggregator.AND,
                        conditions=[
                            ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=1),
                            ConditionTreeLeaf(field="stock", operator=Operator.EQUAL, value=12),
                        ],
                    ),
                    ConditionTreeLeaf("id", Operator.EQUAL, 2),
                ],
            )
        ]
    )

    fields = ["id", "stock"]
    values = [[1, 12], [2, 3]]
    res = ConditionTreeFactory._match_fields(fields, values)
    assert res == ConditionTreeFactory.union(
        [
            ConditionTreeBranch(
                aggregator=Aggregator.OR,
                conditions=[
                    ConditionTreeBranch(
                        aggregator=Aggregator.AND,
                        conditions=[
                            ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=1),
                            ConditionTreeLeaf(field="stock", operator=Operator.EQUAL, value=12),
                        ],
                    ),
                    ConditionTreeBranch(
                        aggregator=Aggregator.AND,
                        conditions=[
                            ConditionTreeLeaf(field="id", operator=Operator.EQUAL, value=2),
                            ConditionTreeLeaf(field="stock", operator=Operator.EQUAL, value=3),
                        ],
                    ),
                ],
            )
        ]
    )


@mock.patch(
    "forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory.ConditionTreeFactory.from_plain_object"
)
def test_from_branch_plain_object(from_plain_component_mock: mock.Mock):
    from_plain_component_mock.side_effect = [ConditionTreeLeaf("id", Operator.EQUAL, 1)]
    assert ConditionTreeFactory._from_branch_plain_object(
        {
            "aggregator": "or",
            "conditions": [{"field": "id", "operator": "equal", "value": 1}],
        }
    ) == ConditionTreeLeaf("id", Operator.EQUAL, 1)
    from_plain_component_mock.assert_has_calls([mock.call({"field": "id", "operator": "equal", "value": 1})])

    from_plain_component_mock.reset_mock()
    from_plain_component_mock.side_effect = [
        ConditionTreeLeaf("id", Operator.EQUAL, 1),
        ConditionTreeLeaf("id", Operator.IN, [1]),
    ]

    assert ConditionTreeFactory._from_branch_plain_object(
        {
            "aggregator": "or",
            "conditions": [
                {"field": "id", "operator": "equal", "value": 1},
                {"field": "id", "operator": "in", "value": [1]},
            ],
        }
    ) == ConditionTreeBranch(
        aggregator=Aggregator.OR,
        conditions=[
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
        ],
    )
    from_plain_component_mock.assert_has_calls(
        [
            mock.call({"field": "id", "operator": "equal", "value": 1}),
            mock.call({"field": "id", "operator": "in", "value": [1]}),
        ]
    )


def test_group():
    assert ConditionTreeFactory._group(
        Aggregator.OR, [ConditionTreeLeaf("id", Operator.EQUAL, 1)]
    ) == ConditionTreeLeaf("id", Operator.EQUAL, 1)

    assert ConditionTreeFactory._group(
        Aggregator.OR,
        [
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
        ],
    ) == ConditionTreeBranch(
        aggregator=Aggregator.OR,
        conditions=[
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
        ],
    )

    assert ConditionTreeFactory._group(
        Aggregator.OR,
        [
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
            ConditionTreeBranch(
                aggregator=Aggregator.OR,
                conditions=[
                    ConditionTreeLeaf("id", Operator.EQUAL, 1),
                    ConditionTreeLeaf("id", Operator.IN, [1]),
                ],
            ),
        ],
    ) == ConditionTreeBranch(
        aggregator=Aggregator.OR,
        conditions=[
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
        ],
    )

    assert ConditionTreeFactory._group(
        Aggregator.OR,
        [
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
            ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeLeaf("id", Operator.EQUAL, 1),
                    ConditionTreeLeaf("id", Operator.IN, [1]),
                ],
            ),
        ],
    ) == ConditionTreeBranch(
        aggregator=Aggregator.OR,
        conditions=[
            ConditionTreeLeaf("id", Operator.EQUAL, 1),
            ConditionTreeLeaf("id", Operator.IN, [1]),
            ConditionTreeBranch(
                aggregator=Aggregator.AND,
                conditions=[
                    ConditionTreeLeaf("id", Operator.EQUAL, 1),
                    ConditionTreeLeaf("id", Operator.IN, [1]),
                ],
            ),
        ],
    )
