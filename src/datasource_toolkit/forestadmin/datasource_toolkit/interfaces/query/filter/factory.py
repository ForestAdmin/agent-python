import sys
from typing import List, Union, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, ManyToMany, OneToMany, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.comparison import Alternative
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.transforms.time import (
    SHIFTED_OPERATORS,
    time_transforms,
)
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter, is_filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils


class FilterFactoryException(DatasourceToolkitException):
    pass


class FilterFactory:
    @staticmethod
    def _shift_period_filter(tz: zoneinfo.ZoneInfo):
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
    def get_previous_period_filter(cls, filter_: Filter) -> Filter:
        if not filter_.condition_tree:
            raise FilterFactoryException("Unable to shift a filter without condition_tree")

        filter_ = filter_.override(
            {
                "condition_tree": filter_.condition_tree.replace(
                    cls._shift_period_filter(filter_.timezone or zoneinfo.ZoneInfo("UTC"))
                )
            }
        )

        return filter_

    @classmethod
    async def make_through_filter(
        cls,
        caller: User,
        collection: Collection,
        id_: CompositeIdAlias,
        relation_name: str,
        _base_foreign_key_filter: Union[PaginatedFilter, Filter],
    ) -> PaginatedFilter:
        if is_filter(_base_foreign_key_filter):
            base_foreign_key_filter: PaginatedFilter = PaginatedFilter.from_base_filter(_base_foreign_key_filter)
        else:
            base_foreign_key_filter = cast(PaginatedFilter, _base_foreign_key_filter)

        relation = collection.schema["fields"][relation_name]
        foreign_relation = CollectionUtils.get_through_target(collection, relation_name)

        # Optimization for many to many when there is not search/segment (saves one query)
        origin_value = await CollectionUtils.get_value(caller, collection, id_, relation["origin_key_target"])
        if foreign_relation and base_foreign_key_filter.is_nestable:
            foreign_key_schema = collection.datasource.get_collection(relation["through_collection"]).schema["fields"][
                relation["foreign_key"]
            ]
            base_through_filter = base_foreign_key_filter.nest(foreign_relation)
            condition_tree = ConditionTreeFactory.intersect(
                [
                    ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value),
                    base_through_filter.condition_tree,
                ]
            )
            if (
                foreign_key_schema["type"] == FieldType.COLUMN
                and Operator.PRESENT in foreign_key_schema["filter_operators"]
            ):
                present = ConditionTreeLeaf(relation["foreign_key"], Operator.PRESENT)
                condition_tree = ConditionTreeFactory.intersect([condition_tree, present])
            return base_through_filter.override({"condition_tree": condition_tree})

        # Otherwise we have no choice but to call the target collection so that search and segment
        # are correctly apply, and then match ids in the though collection.
        target = collection.datasource.get_collection(relation["foreign_collection"])
        records = await target.list(
            caller,
            await cls.make_foreign_filter(caller, collection, id_, relation, base_foreign_key_filter),
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
        caller: User,
        collection: Collection,
        id: CompositeIdAlias,
        relation: Union[ManyToMany, OneToMany],
        _base_foreign_key_filter: Union[PaginatedFilter, Filter],
    ) -> PaginatedFilter:
        if is_filter(_base_foreign_key_filter):
            base_foreign_key_filter: PaginatedFilter = PaginatedFilter.from_base_filter(_base_foreign_key_filter)
        else:
            base_foreign_key_filter = cast(PaginatedFilter, _base_foreign_key_filter)
        origin_value = await CollectionUtils.get_value(caller, collection, id, relation["origin_key_target"])

        # Compute condition tree to match parent record.
        origin_tree: ConditionTree

        if relation["type"] == FieldType.ONE_TO_MANY:
            # OneToMany case (can be done in one request all the time)
            origin_tree = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)
        else:
            # ManyToMany case (more complicated...)
            through = collection.datasource.get_collection(relation["through_collection"])
            foreign_key_schema = through.schema["fields"][relation["foreign_key"]]
            through_tree = ConditionTreeLeaf(relation["origin_key"], Operator.EQUAL, origin_value)

            # Handle null foreign key case only when the datasource supports it.
            if (
                foreign_key_schema["type"] == FieldType.COLUMN
                and Operator.PRESENT in foreign_key_schema["filter_operators"]
            ):
                through_tree = ConditionTreeFactory.intersect(
                    [through_tree, ConditionTreeLeaf(relation["foreign_key"], Operator.PRESENT)]
                )

            records = await through.list(
                caller,
                PaginatedFilter({"condition_tree": through_tree}),
                Projection(relation["foreign_key"]),
            )
            origin_tree = ConditionTreeLeaf(
                relation["foreign_key_target"],
                Operator.IN,
                # filter out null values in case the 'Present' operator was not supported
                [record[relation["foreign_key"]] for record in records if record.get(relation["foreign_key"])],
            )
        trees: List[ConditionTree] = [origin_tree]
        if base_foreign_key_filter.condition_tree:
            trees = [base_foreign_key_filter.condition_tree, *trees]

        return base_foreign_key_filter.override({"condition_tree": ConditionTreeFactory.intersect(trees)})
