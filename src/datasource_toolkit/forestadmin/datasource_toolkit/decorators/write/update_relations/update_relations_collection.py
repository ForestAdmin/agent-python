from functools import reduce
from typing import List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import FieldType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


class UpdateRelationsCollection(CollectionDecorator):
    async def update(self, caller: User, _filter: Optional[Filter], patch: RecordsDataAlias):
        fields_schema = self.schema["fields"]

        # Step 1: Perform the normal update
        patch_without_relations = reduce(
            lambda memo, key: {**memo, key: patch[key]} if fields_schema[key]["type"] == FieldType.COLUMN else memo,
            patch.keys(),
            {},
        )
        if len(patch_without_relations.keys()) > 0:
            await self.child_collection.update(caller, _filter, patch_without_relations)

        # Step 2: Perform additional updates for relations
        relation_keys = [key for key in patch.keys() if fields_schema[key]["type"] != FieldType.COLUMN]
        if len(relation_keys) > 0:
            # Fetch the records that will be updated, to know which relations need to be created/updated
            projection = self.__build_projection(patch)
            records = await self.child_collection.list(caller, PaginatedFilter.from_base_filter(_filter), projection)

            for relation_key in relation_keys:
                await self.__create_or_update_relation(caller, records, relation_key, patch[relation_key])

    def __build_projection(self, patch: RecordsDataAlias) -> Projection:
        """
        Build a projection that has enough information to know
        - which relations need to be created/updated
        - the values that will be used to build filters to target records
        - the values that will be used to create/update the relations
        """
        projection = Projection().with_pks(self)

        for key in patch.keys():
            field_schema = self.schema["fields"][key]
            if field_schema["type"] != FieldType.COLUMN:
                relation = self.datasource.get_collection(field_schema["foreign_collection"])

                projection = projection.union(Projection().with_pks(relation).nest(key))
                if field_schema["type"] == FieldType.MANY_TO_ONE:
                    projection = projection.union(Projection(field_schema["foreign_key_target"]).nest(key))
                elif field_schema["type"] == FieldType.ONE_TO_ONE:
                    projection = projection.union(Projection(field_schema["origin_key_target"]).nest(key))
        return projection

    async def __create_or_update_relation(
        self, caller: User, records: List[RecordsDataAlias], key: str, patch: RecordsDataAlias
    ):
        field_schema = self.schema["fields"][key]
        relation: Collection = self.datasource.get_collection(field_schema["foreign_collection"])

        creates = [*filter(lambda record: record.get(key) is None, records)]
        updates = [*filter(lambda record: record.get(key) is not None, records)]

        if len(creates) > 0:
            if field_schema["type"] == FieldType.MANY_TO_ONE:
                # Create many-to-one relations
                sub_record = await relation.create(caller, [patch])
                sub_record = sub_record[0]
                condition_tree = ConditionTreeFactory.match_records(relation.schema, creates)
                parent_patch = {field_schema["foreign_key"]: sub_record[field_schema["foreign_key_target"]]}

                await self.update(caller, Filter({"condition_tree": condition_tree}), parent_patch)
            else:
                # Create the one-to-one relations that don't already exist
                await relation.create(
                    caller,
                    [
                        {**patch, field_schema["origin_key"]: create[field_schema["origin_key_target"]]}
                        for create in creates
                    ],
                )

        # Update the relations that already exist
        if len(updates) > 0:
            sub_records = [update[key] for update in updates]
            condition_tree = ConditionTreeFactory.match_records(relation.schema, sub_records)

            await relation.update(caller, Filter({"condition_tree": condition_tree}), patch)
