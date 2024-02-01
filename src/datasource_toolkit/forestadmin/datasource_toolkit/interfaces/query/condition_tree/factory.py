from collections import defaultdict
from typing import Any, DefaultDict, List, Optional, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import Column, Operator
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import (
    Aggregator,
    BranchComponents,
    ConditionTreeBranch,
    is_branch_component,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
    is_leaf_component,
)
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias, RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class ConditionTreeFactoryException(DatasourceToolkitException):
    pass


class ConditionTreeFactory:
    MATCH_NONE: ConditionTree = ConditionTreeBranch(Aggregator.OR, [])
    MATCH_ALL: Optional[ConditionTree] = None

    @classmethod
    def match_records(cls, schema: CollectionSchema, records: List[RecordsDataAlias]) -> ConditionTree:
        ids = [RecordUtils.get_primary_key(schema, record) for record in records]
        return cls.match_ids(schema, ids)

    @classmethod
    def match_ids(cls, schema: CollectionSchema, ids: List[CompositeIdAlias]) -> ConditionTree:
        primary_key_names = SchemaUtils.get_primary_keys(schema)
        if not primary_key_names:
            raise ConditionTreeFactoryException("Collection must have at least one primary key")

        for name in primary_key_names:
            operators = cast(Column, schema["fields"][name])["filter_operators"]
            if not operators or not (Operator.EQUAL in operators or Operator.IN in operators):
                raise ConditionTreeFactoryException(f"Field {name} must support opperators: [equal, in]")
        res = cls._match_fields(primary_key_names, ids)
        return res

    @classmethod
    def union(cls, trees: List[ConditionTree]) -> ConditionTree:
        return ConditionTreeFactory._group(Aggregator.OR, trees)

    @classmethod
    def intersect(cls, trees: List[ConditionTree]) -> ConditionTree:
        result = ConditionTreeFactory._group(Aggregator.AND, trees)
        if isinstance(result, ConditionTreeBranch) and len(result.conditions) == 0:
            return None
        return result

    @classmethod
    def from_plain_object(cls, json: Any) -> ConditionTree:
        if is_leaf_component(json):
            return ConditionTreeLeaf.load(json)
        elif is_branch_component(json):
            return cls._from_branch_plain_object(json)
        raise ConditionTreeFactoryException("Failed to instantiate condition tree from json")

    @classmethod
    def _match_fields(cls, fields: List[str], values: List[List[Any]]) -> ConditionTree:
        if not values:
            return cls.MATCH_NONE
        if len(fields) == 1:
            field_values = [value[0] for value in values if len(value)]
            if len(field_values) > 1:
                condition_tree = ConditionTreeLeaf(fields[0], Operator.IN, field_values)
            elif field_values:
                condition_tree = ConditionTreeLeaf(fields[0], Operator.EQUAL, field_values[0])
            else:
                raise
            return condition_tree

        [first_field, *other_fields] = fields
        groups: DefaultDict[Any, List[List[Any]]] = defaultdict(list)

        for [first_value, *other_values] in values:
            groups[first_value].append(other_values)

        intersect_results: List[ConditionTree] = []
        for first_value, sub_values in groups.items():
            leaf: ConditionTree = ConditionTreeFactory._match_fields([first_field], [[first_value]])
            try:
                tree: ConditionTree = ConditionTreeFactory._match_fields(other_fields, sub_values)
            except Exception:
                intersect_result = leaf
            else:
                intersect_result = ConditionTreeFactory.intersect([leaf, tree])
            if intersect_result:
                intersect_results.append(intersect_result)

        return ConditionTreeFactory.union(intersect_results)

    @classmethod
    def _from_branch_plain_object(cls, json: BranchComponents) -> ConditionTree:
        sub_trees = [cls.from_plain_object(sub_tree) for sub_tree in json["conditions"]]
        branch = ConditionTreeBranch(Aggregator(json["aggregator"]), sub_trees)
        if len(branch.conditions) == 1:
            return branch.conditions[0]
        return branch

    @staticmethod
    def _group(aggregator: Aggregator, trees: List[ConditionTree]) -> ConditionTree:
        conditions: List[ConditionTree] = []
        for tree in trees:
            if tree is None:
                continue
            if isinstance(tree, ConditionTreeBranch) and tree.aggregator == aggregator:
                conditions.extend(tree.conditions)
            else:
                conditions.append(tree)

        if len(conditions) == 1:
            return conditions[0]

        return ConditionTreeBranch(aggregator, conditions)
