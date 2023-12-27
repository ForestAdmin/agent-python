from typing import Any, Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.exceptions import ComputedDecoratorException
from forestadmin.datasource_toolkit.decorators.computed.helpers import compute_from_records, rewrite_fields
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldType, RelationAlias
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.field import FieldValidator
from typing_extensions import Self


class ComputedCollectionDecorator(CollectionDecorator):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._computeds: Dict[str, ComputedDefinition] = {}

    def get_computed(self, path: str) -> Union[ComputedDefinition, None]:
        if ":" not in path:
            try:
                return self._computeds[path]
            except KeyError:
                return None

        related_field, path = path.split(":", 1)
        field = cast(RelationAlias, self.get_field(related_field))
        foreign_collection: Self = self.datasource.get_collection(field["foreign_collection"])
        return foreign_collection.get_computed(path)

    def register_computed(self, name: str, computed: ComputedDefinition):
        if computed.get("dependencies") is None or len(computed["dependencies"]) == 0:
            raise ComputedDecoratorException(f"Computed field '{self.name}.{name}' must have at least one dependency")
        FieldValidator.validate_name(self.name, name)
        for field in computed["dependencies"]:
            try:
                FieldValidator.validate(self.child_collection, field)  # type: ignore
            except DatasourceToolkitException:
                raise ComputedDecoratorException(
                    f"The dependency {field} of the computed field {name} is unknown in the collection {self.name}"
                )
        self._computeds[name] = computed
        self.mark_schema_as_dirty()

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        new_projection = projection.replace(lambda path: rewrite_fields(self, path))
        records: List[Optional[RecordsDataAlias]] = await super().list(caller, _filter, new_projection)  # type: ignore
        if new_projection == projection:
            return records

        context = CollectionCustomizationContext(cast(Collection, self), caller)
        return await compute_from_records(context, self, new_projection, projection, records)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        if not any([self.get_computed(field) for field in aggregation.projection]):
            return await self.child_collection.aggregate(caller, _filter, aggregation, limit)

        records = await self.list(caller, PaginatedFilter.from_base_filter(_filter), aggregation.projection)
        return aggregation.apply(records, caller.timezone, limit)

    def _refine_schema(self, sub_schema: CollectionSchema) -> CollectionSchema:
        computed_fields_schema = {**sub_schema["fields"]}
        for name, computed in self._computeds.items():
            computed_fields_schema[name] = {
                "column_type": computed["column_type"],
                "default_value": computed.get("default_value", None),
                "type": FieldType.COLUMN,
                "enum_values": computed.get("enum_values", None),
                "filter_operators": set(),
                "is_primary_key": False,
                "is_read_only": True,
                "is_sortable": False,
                "validations": [],
            }
        return {**sub_schema, "fields": computed_fields_schema}
