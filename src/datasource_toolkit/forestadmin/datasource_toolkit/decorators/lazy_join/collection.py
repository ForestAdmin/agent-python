from typing import List, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import ManyToOne, is_many_to_one
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

        return self._apply_joins_on_records(projection, simplified_projection, ret)

    async def _refine_filter(
        self, caller: User, _filter: Union[Filter, PaginatedFilter, None]
    ) -> Union[Filter, PaginatedFilter, None]:
        if _filter is None or _filter.condition_tree is None:
            return _filter

        _filter.condition_tree = _filter.condition_tree.replace(
            lambda leaf: (
                ConditionTreeLeaf(
                    self._get_fk_field_for_projection(leaf.field),
                    leaf.operator,
                    leaf.value,
                )
                if self._is_useless_join(leaf.field.split(":")[0], _filter.condition_tree.projection)
                else leaf
            )
        )

        return _filter

    def _is_useless_join(self, relation: str, projection: Projection) -> bool:
        relation_schema = self.schema["fields"][relation]
        sub_projections = projection.relations[relation]

        return (
            is_many_to_one(relation_schema)
            and len(sub_projections) == 1
            and sub_projections[0] == relation_schema["foreign_key_target"]
        )

    def _get_fk_field_for_projection(self, projection: str) -> str:
        relation_name = projection.split(":")[0]
        relation_schema = cast(ManyToOne, self.schema["fields"][relation_name])

        return relation_schema["foreign_key"]

    def _get_projection_without_useless_joins(self, projection: Projection) -> Projection:
        returned_projection = Projection(*projection)
        for relation, relation_projections in projection.relations.items():
            if self._is_useless_join(relation, projection):
                # remove foreign key target from projection
                returned_projection.remove(f"{relation}:{relation_projections[0]}")

                # add foreign keys to projection
                fk_field = self._get_fk_field_for_projection(relation)
                if fk_field not in returned_projection:
                    returned_projection.append(fk_field)

        return returned_projection

    def _apply_joins_on_records(
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
                    record[relation] = {
                        relation_projections[0]: record[
                            self._get_fk_field_for_projection(f"{relation}:{relation_projections[0]}")
                        ]
                    }

            # remove foreign keys
            for projection in projections_to_rm:
                del record[projection]

        return records
