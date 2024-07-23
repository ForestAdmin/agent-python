from typing import Any, Dict, List, Optional, Union, cast

from forestadmin.agent_toolkit.forest_logger import ForestLogger
from forestadmin.agent_toolkit.utils.context import User
from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.collection_decorator import CollectionDecorator
from forestadmin.datasource_toolkit.decorators.computed.exceptions import ComputedDecoratorException
from forestadmin.datasource_toolkit.decorators.computed.helpers.compute_fields import compute_from_records
from forestadmin.datasource_toolkit.decorators.computed.helpers.rewrite_projection import rewrite_fields
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import (
    ColumnAlias,
    FieldType,
    PrimitiveType,
    RelationAlias,
    is_polymorphic_many_to_one,
)
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

    def get_computed(self, path_p: str) -> Union[ComputedDefinition, None]:
        if ":" not in path_p:
            return self._computeds.get(path_p)

        related_field, path = path_p.split(":", 1)
        field = cast(RelationAlias, self.get_field(related_field))
        if is_polymorphic_many_to_one(field):
            ForestLogger.log(
                "debug", f"Cannot compute computed fields over polymorphic relation {self.name}.{related_field}."
            )
            return None

        foreign_collection: Self = self.datasource.get_collection(field["foreign_collection"])
        return foreign_collection.get_computed(path)

    def register_computed(self, name: str, computed: ComputedDefinition):
        if computed.get("dependencies") is None or len(computed["dependencies"]) == 0:
            raise ComputedDecoratorException(f"Computed field '{self.name}.{name}' must have at least one dependency")

        FieldValidator.validate_name(self.name, name)

        for field in computed["dependencies"]:
            FieldValidator.validate(self, field)
            if ":" in field and is_polymorphic_many_to_one(self.schema["fields"][field.split(":")[0]]):
                raise ComputedDecoratorException(
                    f"Dependencies over a polymorphic relations({self.name}.{field.split(':')[0]}) are forbidden."
                )

        # cast
        column_type = ComputedCollectionDecorator._cast_column_type(computed["column_type"])

        self._computeds[name] = cast(ComputedDefinition, {**computed, "column_type": column_type})
        self.mark_schema_as_dirty()

    async def list(self, caller: User, _filter: PaginatedFilter, projection: Projection) -> List[RecordsDataAlias]:
        new_projection = projection.replace(lambda path: rewrite_fields(self, path))
        records: List[RecordsDataAlias] = await super().list(caller, _filter, new_projection)  # type: ignore
        if new_projection == projection:
            return records

        context = CollectionCustomizationContext(cast(Collection, self), caller)
        return await compute_from_records(context, self, new_projection, projection, records)

    async def aggregate(
        self, caller: User, _filter: Optional[Filter], aggregation: Aggregation, limit: Optional[int] = None
    ) -> List[AggregateResult]:
        if not any([self.get_computed(field) for field in aggregation.projection]):
            return await self.child_collection.aggregate(caller, _filter, aggregation, limit)

        return aggregation.apply(
            await self.list(caller, PaginatedFilter.from_base_filter(_filter), aggregation.projection),
            str(caller.timezone),
            limit,
        )

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

    @staticmethod
    def _cast_column_type(
        column_type_input: ColumnAlias,
    ) -> Union[PrimitiveType, Dict[str, PrimitiveType], List[PrimitiveType], List[Dict[str, PrimitiveType]]]:
        """to allow user to declare column type as string instead of PrimitiveType enum"""
        if isinstance(column_type_input, dict):
            column_type = {k: ComputedCollectionDecorator._cast_column_type(t) for k, t in column_type_input.items()}
        elif isinstance(column_type_input, list):
            column_type = [ComputedCollectionDecorator._cast_column_type(column) for column in column_type_input]
        else:
            column_type = PrimitiveType(column_type_input)
        return column_type  # type:ignore
