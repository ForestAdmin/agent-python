from typing import Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import ManyToOne, is_many_to_one
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class LazyJoinCollectionDecorator(CollectionDecorator):
    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        simplified_projection = self._get_projection_without_useless_joins(projection)

        refined_filter = cast(PaginatedFilter, await self._refine_filter(caller, filter_))
        ret = await self.child_collection.list(caller, refined_filter, simplified_projection)

        return self._apply_joins_on_simplified_records(projection, simplified_projection, ret)

    async def _refine_filter(
        self, caller: User, _filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        if _filter is None or _filter.condition_tree is None:
            return _filter

        _filter.condition_tree = _filter.condition_tree.replace(
            lambda leaf: (
                ConditionTreeLeaf(
                    self._get_fk_field_for_many_to_one_projection(leaf.field),
                    leaf.operator,
                    leaf.value,
                )
                if self._is_useless_join_for_projection(leaf.field.split(":")[0], _filter.condition_tree.projection)
                else leaf
            )
        )

        return _filter

    async def aggregate(
        self, caller: User, filter_: Union[Filter, None], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        replaced = {}  # new_name -> old_name; for a simpler reconciliation

        def replacer(field_name: str) -> str:
            if self._is_useless_join_for_projection(field_name.split(":")[0], aggregation.projection):
                new_field_name = self._get_fk_field_for_many_to_one_projection(field_name)
                replaced[new_field_name] = field_name
                return new_field_name
            return field_name

        new_aggregation = aggregation.replace_fields(replacer)

        aggregate_results = await self.child_collection.aggregate(
            caller, cast(Filter, await self._refine_filter(caller, filter_)), new_aggregation, limit
        )
        if aggregation == new_aggregation:
            return aggregate_results
        return self._replace_fields_in_aggregate_group(aggregate_results, replaced)

    def _is_useless_join_for_projection(self, relation: str, projection: Projection) -> bool:
        relation_schema = self.schema["fields"][relation]
        sub_projections = projection.relations[relation]

        return (
            is_many_to_one(relation_schema)
            and len(sub_projections) == 1
            and sub_projections[0] == relation_schema["foreign_key_target"]
        )

    def _get_fk_field_for_many_to_one_projection(self, projection: str) -> str:
        relation_name = projection.split(":")[0]
        relation_schema = cast(ManyToOne, self.schema["fields"][relation_name])

        return relation_schema["foreign_key"]

    def _get_projection_without_useless_joins(self, projection: Projection) -> Projection:
        returned_projection = Projection(*projection)
        for relation, relation_projections in projection.relations.items():
            if self._is_useless_join_for_projection(relation, projection):
                # remove foreign key target from projection
                returned_projection.remove(f"{relation}:{relation_projections[0]}")

                # add foreign keys to projection
                fk_field = self._get_fk_field_for_many_to_one_projection(f"{relation}:{relation_projections[0]}")
                if fk_field not in returned_projection:
                    returned_projection.append(fk_field)

        return returned_projection

    def _apply_joins_on_simplified_records(
        self, initial_projection: Projection, requested_projection: Projection, records: List[RecordsDataAlias]
    ) -> List[RecordsDataAlias]:
        if requested_projection == initial_projection:
            return records

        projections_to_add = Projection(*[p for p in initial_projection if p not in requested_projection])
        projections_to_rm = Projection(*[p for p in requested_projection if p not in initial_projection])

        for record in records:
            # add to records relation:id
            for relation, relation_projections in projections_to_add.relations.items():
                relation_schema = self.schema["fields"][relation]

                if is_many_to_one(relation_schema):
                    fk_value = record[
                        self._get_fk_field_for_many_to_one_projection(f"{relation}:{relation_projections[0]}")
                    ]
                    record[relation] = {relation_projections[0]: fk_value} if fk_value else None

            # remove foreign keys
            for projection in projections_to_rm:
                del record[projection]

        return records

    def _replace_fields_in_aggregate_group(
        self, aggregate_results: List[AggregateResult], field_to_replace: Dict[str, str]
    ) -> List[AggregateResult]:
        for aggregate_result in aggregate_results:
            group = {}
            for field, value in aggregate_result["group"].items():
                if field in field_to_replace:
                    group[field_to_replace[field]] = value
                else:
                    group[field] = value
            aggregate_result["group"] = group

        return aggregate_results
