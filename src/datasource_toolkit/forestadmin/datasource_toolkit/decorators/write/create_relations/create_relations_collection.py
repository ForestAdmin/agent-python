from typing import Dict, List, TypedDict

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, ManyToOne, OneToOne, Operator
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias

RecordWithIndex = TypedDict("RecordWithIndex", {"sub_record": RecordsDataAlias, "index": int})


class CreateRelationsCollection(CollectionDecorator):
    async def create(self, caller: User, data: List[RecordsDataAlias]) -> List[RecordsDataAlias]:
        # Step 1: Remove all relations from records, and store them in a map
        records_by_relation = self.__extract_relations(data)

        # Step 2: Create the many-to-one relations, and put the foreign keys in the records
        for field_name, entries in records_by_relation.items():
            if self.schema["fields"].get(field_name, {}).get("type") == FieldType.MANY_TO_ONE:
                await self.__create_many_to_one_relation(caller, data, field_name, entries)

        # Step 3: Create the records
        records_with_pk = await self.child_collection.create(caller, data)

        # Step 4: Create the one-to-one relations
        # Note: the createOneToOneRelation method modifies the records_with_pk array in place!
        for field_name, entries in records_by_relation.items():
            if self.schema["fields"].get(field_name, {}).get("type") == FieldType.ONE_TO_ONE:
                await self.__create_one_to_one_relation(caller, records_with_pk, field_name, entries)

        return records_with_pk

    def __extract_relations(self, records: List[RecordsDataAlias]) -> Dict[str, List[RecordWithIndex]]:
        records_by_relation = {}

        for index, record in enumerate([*records]):  # prevent "size change during iteration" error
            for field_name, sub_record in {**record}.items():  # prevent "size change during iteration" error
                if self.schema["fields"].get(field_name, {"type": None})["type"] != FieldType.COLUMN:
                    if records_by_relation.get(field_name) is None:
                        records_by_relation[field_name] = []
                    records_by_relation[field_name].append({"sub_record": sub_record, "index": index})
                    del records[index][field_name]
        return records_by_relation

    async def __create_many_to_one_relation(
        self, caller: User, records: List[RecordsDataAlias], field_name: str, entries: List[RecordWithIndex]
    ):
        field_schema: ManyToOne = self.schema["fields"][field_name]
        relation: Collection = self.datasource.get_collection(field_schema["foreign_collection"])

        creations = [entry for entry in entries if records[entry["index"]].get(field_schema["foreign_key"]) is None]
        updates = [entry for entry in entries if records[entry["index"]].get(field_schema["foreign_key"]) is not None]

        # Create the relations when the fk is not present
        if len(creations) > 0:
            # Not sure which behavior is better (we'll go with the first option for now):
            # - create a new record for each record in the original create request
            # - use object-hash to create a single record for each unique subRecord
            sub_records = [creation["sub_record"] for creation in creations]
            related_records = await relation.create(caller, sub_records)

            for creation in creations:
                index = creation["index"]
                records[index][field_schema["foreign_key"]] = related_records[index][field_schema["foreign_key_target"]]

        # Update the relations when the fk is present
        for update in updates:
            value = records[update["index"]][field_schema["foreign_key"]]
            condition_tree = ConditionTreeLeaf(field_schema["foreign_key_target"], Operator.EQUAL, value)

            await relation.update(caller, Filter({"condition_tree": condition_tree}), update["sub_record"])

    async def __create_one_to_one_relation(
        self, caller: User, records: List[RecordsDataAlias], field_name: str, entries: List[RecordWithIndex]
    ):
        field_schema: OneToOne = self.schema["fields"][field_name]
        relation: Collection = self.datasource.get_collection(field_schema["foreign_collection"])

        # Set origin key in the related record
        sub_records = [
            {
                **entry["sub_record"],
                field_schema["origin_key"]: records[entry["index"]][field_schema["origin_key_target"]],
            }
            for entry in entries
        ]

        await relation.create(caller, sub_records)
