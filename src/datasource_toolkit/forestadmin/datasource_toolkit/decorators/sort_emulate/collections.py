from typing import Dict, List, Optional

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.exceptions import ForestException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, FieldType, RelationAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema, Datasource
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import PlainSortClause, Sort
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from forestadmin.datasource_toolkit.validations.field import FieldValidator


class SortCollectionDecorator(CollectionDecorator):
    def __init__(self, collection: Collection, datasource: Datasource):
        super().__init__(collection, datasource)
        self._sorts: Dict[str, Sort] = {}
        self._disabled_sorts: List[str] = []

    def emulate_field_sorting(self, name: str):
        self.__replace_or_emulate_field_sorting(name, None)

    def replace_field_sorting(self, name: str, equivalent_sort: Optional[List[PlainSortClause]] = None):
        if not equivalent_sort:
            raise ForestException("A new sorting method should be provided to replace field sorting")
        self.__replace_or_emulate_field_sorting(name, equivalent_sort)

    def __replace_or_emulate_field_sorting(self, name: str, equivalent_sort: Optional[List[PlainSortClause]]):
        FieldValidator.validate(self, name)

        self._sorts[name] = Sort(equivalent_sort) if equivalent_sort else None
        self.mark_schema_as_dirty()

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        fields: Dict[str, FieldAlias] = {}

        for name, schema in sub_schema["fields"].items():
            if name in self._sorts.keys() and schema["type"] == FieldType.COLUMN:
                fields[name] = {**schema, "is_sortable": True}
            else:
                fields[name] = schema

        return {**sub_schema, "fields": fields}

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        if _filter.sort:
            child_filter = _filter.override(
                {"sort": _filter.sort.replace_clauses(lambda clause: self.rewrite_plain_sort_clause(clause))}
            )
        else:
            child_filter = _filter

        if not (child_filter.sort and any(map(lambda field: self._is_emulated(field["field"]), child_filter.sort))):
            return await self.child_collection.list(caller, child_filter, projection)

        # Fetch the whole collection, but only with the fields we need to sort
        reference_records: List[RecordsDataAlias] = await self.child_collection.list(
            caller, child_filter.override({"sort": None, "page": None}), child_filter.sort.projection.with_pks(self)
        )

        reference_records = child_filter.sort.apply(reference_records)
        if child_filter.page:
            reference_records = child_filter.page.apply(reference_records)

        # We now have the information we need to sort by the field
        new_filter = PaginatedFilter(
            {"condition_tree": ConditionTreeFactory.match_records(self.schema, reference_records)}
        )

        records = await self.child_collection.list(caller, new_filter, projection.with_pks(self))
        records = self._sort_records(reference_records, records)
        records = projection.apply(records)

        return records

    def _sort_records(
        self, reference_records: List[RecordsDataAlias], records: List[RecordsDataAlias]
    ) -> List[RecordsDataAlias]:
        position_by_id = {}
        sorted_ = [None for r in reference_records]

        for index, record in enumerate(reference_records):
            id_ = "|".join([str(pk) for pk in RecordUtils.get_primary_key(self.schema, record)])
            position_by_id[id_] = index

        for record in records:
            id_ = "|".join([str(pk) for pk in RecordUtils.get_primary_key(self.schema, record)])
            sorted_[position_by_id[id_]] = record
        return sorted_

    def rewrite_plain_sort_clause(self, clause: PlainSortClause) -> Sort:
        # Order by is targeting a field on another collection => recurse.
        if ":" in clause["field"]:
            prefix = clause["field"].split(":")[0]
            schema: RelationAlias = self.schema["fields"][prefix]
            association = self.datasource.get_collection(schema["foreign_collection"])

            return (
                Sort([clause])
                .unnest()
                .replace_clauses(lambda sub_clause: association.rewrite_plain_sort_clause(sub_clause))
                .nest(prefix)
            )

        # Field that we own: recursively replace using equivalent sort
        equivalent_sort = self._sorts.get(clause["field"])
        if equivalent_sort:
            if clause["ascending"] is False:
                equivalent_sort = equivalent_sort.inverse()

            return equivalent_sort.replace_clauses(lambda sub_clause: self.rewrite_plain_sort_clause(sub_clause))

        return Sort([clause])

    def _is_emulated(self, path: str) -> bool:
        if ":" not in path:
            return path in self._sorts.keys()

        foreign_collection = self.schema["fields"][path.split(":")[0]]["foreign_collection"]
        association = self.datasource.get_collection(foreign_collection)

        return association._is_emulated(":".join(path.split(":")[1:]))
