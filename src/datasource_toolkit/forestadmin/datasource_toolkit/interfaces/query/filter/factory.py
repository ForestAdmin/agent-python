from typing import List, Union, cast

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import Alternative
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    SHIFTED_OPERATORS,
    time_transforms,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class FilterFactoryException(DatasourceToolkitException):
    pass


class FilterFactory:
    @staticmethod
    def _shift_period_filter(tz: str):
        def __replace(leaf: ConditionTree) -> ConditionTree:
            leaf = cast(ConditionTreeLeaf, leaf)
            time_transform = time_transforms(1)
            if leaf.operator not in SHIFTED_OPERATORS:
                raise FilterFactoryException(f"'{leaf.operator}' is not shiftable ")

            alternative: Alternative = time_transform[leaf.operator][0]
            leaf = alternative["replacer"](leaf, tz)
            return leaf

        return __replace

    @classmethod
    def get_previous_period_filter(cls, filter: Filter) -> Filter:
        if not filter.condition_tree:
            raise FilterFactoryException("Unable to shift a filter without condition_tree")

        filter = filter.override(
            {"condition_tree": filter.condition_tree.replace(cls._shift_period_filter(filter.timezone or "UTC"))}
        )

        return filter

    @staticmethod
    def _build_for_through_relation(
        base_foreign_key_filter: PaginatedFilter,
        origin_key: str,
        foreign_relation: str,
        origin_value: Union[int, str],
    ):
        base_through_filter = base_foreign_key_filter.nest(foreign_relation)
        leaf = ConditionTreeLeaf(origin_key, Operator.EQUAL, origin_value)
        if not base_through_filter.condition_tree:
            condition_tree = leaf
        else:
            condition_tree = ConditionTreeFactory.intersect(
                [
                    leaf,
                    base_through_filter.condition_tree,
                ]
            )
        return base_through_filter.override({"condition_tree": condition_tree})

    @classmethod
    async def make_through_filter(
        cls,
        collection: Collection,
        id: CompositeIdAlias,
        relation_name: str,
        base_foreign_key_filter: PaginatedFilter,
    ):
        relation = collection.get_field(relation_name)
        if relation["type"] != FieldType.MANY_TO_MANY:
            raise FilterFactoryException("origin_key_targent doesn't exist for this field")
        origin_value = await CollectionUtils.get_value(collection, id, relation["origin_key_target"])
        if relation["foreign_relation"] and base_foreign_key_filter.is_nestable:
            return cls._build_for_through_relation(
                base_foreign_key_filter,
                relation["origin_key"],
                relation["foreign_relation"],
                origin_value,
            )
        target = collection.datasource.get_collection(relation["foreign_collection"])
        records = await target.list(
            await cls.make_foreign_filter(collection, id, relation_name, base_foreign_key_filter),
            Projection(relation["foreign_key_target"]),
        )

        return PaginatedFilter(
            {
                "condition_tree": ConditionTreeFactory.intersect(
                    [
                        ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value),
                        ConditionTreeLeaf(
                            relation["foreign_key"],
                            Operator.IN,
                            [record[relation["foreign_key_target"]] for record in records],
                        ),
                    ]
                )
            }
        )

    @staticmethod
    async def make_foreign_filter(
        collection: Collection,
        id: CompositeIdAlias,
        relation_name: str,
        base_foreign_key_filter: PaginatedFilter,
    ) -> PaginatedFilter:
        relation = SchemaUtils.get_to_many_relation(collection.schema, relation_name)
        origin_value = await CollectionUtils.get_value(collection, id, relation["origin_key_target"])

        origin_tree: ConditionTree

        if relation["type"] == FieldType.ONE_TO_MANY:
            origin_tree = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
        else:
            through = collection.datasource.get_collection(relation["through_collection"])
            through_tree = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
            records = await through.list(
                PaginatedFilter({"condition_tree": through_tree}),
                Projection(relation["foreign_key"]),
            )
            origin_tree = ConditionTreeLeaf(
                relation["foreign_key_target"],
                Operator.IN,
                [record[relation["foreign_key"]] for record in records],
            )
        trees: List[ConditionTree] = [origin_tree]
        if base_foreign_key_filter.condition_tree:
            trees = [base_foreign_key_filter.condition_tree, *trees]

        return base_foreign_key_filter.override({"condition_tree": ConditionTreeFactory.intersect(trees)})
