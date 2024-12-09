from typing import List

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import is_many_to_one
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class PerfOptimizerCollectionDecorator(CollectionDecorator):
    async def list(self, caller: User, filter_: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        simplified_projection = self._get_simplified_projection(projection)

        ret = await super().list(caller, filter_, simplified_projection)

        return self._apply_simplification_to_records(projection, simplified_projection, ret)

    def _get_simplified_projection(self, projection: Projection) -> Projection:
        returned_projection = Projection(*projection)
        for relation, relation_projections in projection.relations.items():
            relation_schema = self.schema["fields"][relation]

            if is_many_to_one(relation_schema):
                if len(relation_projections) == 1 and relation_schema["foreign_key_target"] == relation_projections[0]:
                    returned_projection.remove(f"{relation}:{relation_projections[0]}")

        return returned_projection

    def _apply_simplification_to_records(
        self, desired_projection: Projection, record_projection: Projection, records: List[RecordsDataAlias]
    ) -> List[RecordsDataAlias]:
        if record_projection == desired_projection:
            return records

        projection_differences = Projection(*[p for p in desired_projection if p not in record_projection])

        for relation, relation_projections in projection_differences.relations.items():
            relation_schema = self.schema["fields"][relation]

            if is_many_to_one(relation_schema):
                if len(relation_projections) == 1 and relation_schema["foreign_key_target"] == relation_projections[0]:
                    for record in records:
                        # TODO: verify about this assertion and remove it, or deal it another way
                        assert relation not in record
                        record[relation] = {relation_projections[0]: record[relation_schema["foreign_key_target"]]}

        return records
