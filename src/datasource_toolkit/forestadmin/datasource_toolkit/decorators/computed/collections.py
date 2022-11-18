from typing import Any, Callable, Dict, List, Optional, cast

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.exceptions import ComputedMixinException
from forestadmin.datasource_toolkit.decorators.computed.helpers import (  # type: ignore
    compute_aggregate_from_records,
    compute_from_records,
    computed_aggregation_projection,
    rewrite_fields,
)
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import FieldAlias, FieldType
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
from forestadmin.datasource_toolkit.interfaces.query.aggregation import AggregateResult, Aggregation
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.validations.field import FieldValidator
from typing_extensions import Self


class ComputedMixin:

    name: str
    get_field: Callable[[str], FieldAlias]
    datasource: property
    mark_schema_as_dirty: Callable[..., None]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._computeds: Dict[str, ComputedDefinition] = {}

    def get_computed(self, path: str) -> ComputedDefinition:
        if ":" not in path:
            try:
                return self._computeds[path]
            except KeyError:
                raise ComputedMixinException(f"{path} is not a computed field")

        collection_name, path = path.split(":")
        foreign_collection: Self = self.datasource.get_collection(collection_name)
        return foreign_collection.get_computed(path)

    def register_computed(self, name: str, computed: ComputedDefinition):
        for field in computed["dependencies"]:
            try:
                FieldValidator.validate(self, field)  # type: ignore
            except DatasourceToolkitException:
                raise ComputedMixinException(
                    f"The dependency {field} of the computed field {name} is unknown in the collection {self.name}"
                )
        self._computeds[name] = computed
        self.mark_schema_as_dirty()

    async def list(self, filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        new_projection = projection.replace(lambda path: rewrite_fields(self, path))
        records: List[Optional[RecordsDataAlias]] = await super().list(filter, new_projection)  # type: ignore
        context = CollectionCustomizationContext(cast(Collection, self), filter.timezone)
        return await compute_from_records(context, self, new_projection, projection, records)

    async def aggregate(
        self, filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        is_computed = any([field in self._computeds for field in cast(List[str], aggregation.projection)])
        if is_computed:
            aggregation, new_to_old_group = computed_aggregation_projection(self, aggregation)  # type: ignore
        records: List[AggregateResult] = await super().aggregate(filter, aggregation, limit)  # type: ignore
        if is_computed:
            records = compute_aggregate_from_records(records, new_to_old_group)  # type: ignore
        return records

    @property
    def schema(self) -> CollectionSchema:
        schema: CollectionSchema = super(ComputedMixin, self).schema  # type: ignore
        for name, computed in self._computeds.items():
            schema["fields"][name] = {
                "column_type": computed["column_type"],
                "default_value": computed.get("default_value", None),
                "type": FieldType.COLUMN,
                "enum_values": computed.get("enum_values", None),
                "filter_operators": set(),
                "is_primary_key": False,
                "is_read_only": True,
                "is_sortable": False,
                "validations": None,
            }
        return schema
