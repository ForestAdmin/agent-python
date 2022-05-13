from typing import List, Set, Union, cast

from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    ManyToMany,
    OneToMany,
    Operator,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    ConditionTree,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import (
    ConditionTreeLeaf,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import (
    Alternative,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    time_transforms,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import (
    PaginatedFilter,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class FilterFactory:
    @staticmethod
    def _replace_period_filter(tz: str):
        def __replace(leaf: ConditionTree) -> ConditionTree:
            leaf = cast(ConditionTreeLeaf, leaf)
            time_transform = time_transforms(1)
            allowed_operators: Set[Operator] = time_transform.keys() - [
                Operator.BEFORE,
                Operator.AFTER,
                Operator.PAST,
                Operator.FUTURE,
                Operator.BEFORE_X_HOURS_AGO,
                Operator.AFTER_X_HOURS_AGO,
            ]
            if leaf.operator not in allowed_operators:
                raise

            alternative: Alternative = time_transform[leaf.operator][0]
            leaf = alternative["replacer"](leaf, tz)
            return leaf

        return __replace

    @classmethod
    def get_previous_period_filter(cls, filter: Filter) -> Filter:
        if not filter.condition_tree:
            raise

        filter.override(
            {"condition_tree": filter.condition_tree.replace(cls._replace_period_filter(filter.timezone or "utc"))}
        )

        return filter

    @staticmethod
    def _build_through_filter_for_nestable_many_to_many(
        base_foreign_key_filter: PaginatedFilter,
        origin_key: str,
        foreign_relation: str,
        origin_value: Union[int, str],
    ):
        base_through_filter = base_foreign_key_filter.nest(foreign_relation)
        if not base_through_filter.condition_tree:
            raise
        return base_through_filter.override(
            {
                "condition_tree": ConditionTreeFactory.intersect(
                    [
                        ConditionTreeLeaf(origin_key, Operator.EQUAL, origin_value),
                        base_through_filter.condition_tree,
                    ]
                )
            }
        )

    @classmethod
    async def make_through_filter(
        cls,
        collection: Collection,
        id: CompositeIdAlias,
        relation_name: str,
        base_foreign_key_filter: PaginatedFilter,
    ):

        relation = collection.schema["fields"][relation_name]
        if not isinstance(relation, ManyToMany):
            raise Exception("origin_key_targent doesn't exist for this field")

        origin_value = await CollectionUtils.get_value(collection, id, relation["origin_key_target"])
        if relation["foreign_relation"] and base_foreign_key_filter.is_nestable:
            return cls._build_through_filter_for_nestable_many_to_many(
                base_foreign_key_filter,
                relation["origin_key"],
                relation["foreign_relation"],
                origin_value,
            )

        target = cast(
            Collection,
            collection.datasource.get_collection(relation["foreign_collection"]),
        )

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

        if isinstance(relation, OneToMany):
            origin_tree = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
        else:
            through = cast(
                Collection,
                collection.datasource.get_collection(relation["through_collection"]),
            )
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
            trees.insert(0, base_foreign_key_filter.condition_tree)

        return base_foreign_key_filter.override({"condition_tree": ConditionTreeFactory.intersect(trees)})
