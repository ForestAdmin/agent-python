from typing import List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import is_many_to_one
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class LazyJoinCollectionDecorator(CollectionDecorator):
    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        simplified_projection = self._get_projection_without_useless_joins(projection)

        ret = await super().list(caller, filter_, simplified_projection)

        return self._apply_joins_on_records(projection, simplified_projection, ret)

    def _get_projection_without_useless_joins(self, projection: Projection) -> Projection:
        returned_projection = Projection(*projection)
        for relation, relation_projections in projection.relations.items():
            relation_schema = self.schema["fields"][relation]

            if is_many_to_one(relation_schema):
                if len(relation_projections) == 1 and relation_schema["foreign_key_target"] == relation_projections[0]:
                    # remove foreign key target from projection
                    returned_projection.remove(f"{relation}:{relation_projections[0]}")
                    # add foreign keys to projection
                    if relation_schema["foreign_key"] not in returned_projection:
                        returned_projection.append(relation_schema["foreign_key"])

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
                    record[relation] = {relation_projections[0]: record[relation_schema["foreign_key_target"]]}

            # remove foreign keys
            for projection in projections_to_rm:
                del record[projection]

        return records
