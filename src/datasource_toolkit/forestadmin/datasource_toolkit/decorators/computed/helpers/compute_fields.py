import copy
from typing import Any, List

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.computed.utils.deduplication import Output, transform_unique_values
from forestadmin.datasource_toolkit.decorators.computed.utils.flattener import flatten, unflatten, with_null_markers
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function


async def compute_field(
    context: CollectionCustomizationContext,
    computed: ComputedDefinition,
    paths: List[str],
    dependency_values: List[List[Any]],
) -> List[Output]:
    async def _compute_field_cb(unique_partials: List[RecordsDataAlias]) -> Output:
        ret = await call_user_function(computed["get_values"], unique_partials, context)
        return ret

    return await transform_unique_values(unflatten(dependency_values, Projection(*paths)), _compute_field_cb)


async def queue_field(
    ctx: CollectionCustomizationContext,
    collection: Any,
    new_path: str,
    paths: List[str],
    flatten_records: List[List[Any]],
):
    # Skip double computations (we're not checking before adding to queue).
    if new_path not in paths:
        computed = collection.get_computed(new_path)
        computed_dependencies = with_null_markers(computed["dependencies"])
        nested_dependencies = Projection(*computed_dependencies).nest(
            new_path.rsplit(":", 1)[0] if ":" in new_path else None
        )

        for path in nested_dependencies:
            await queue_field(ctx, collection, path, paths, flatten_records)

        dependency_values = [flatten_records[paths.index(path)] for path in nested_dependencies]
        paths.append(new_path)

        flatten_records.append(
            await compute_field(ctx, computed, computed_dependencies, copy.deepcopy(dependency_values)) or []
        )


async def compute_from_records(
    ctx: CollectionCustomizationContext,
    collection: Any,
    records_projection: Projection,
    desired_projections: Projection,
    records: List[RecordsDataAlias],
) -> List[RecordsDataAlias]:
    # As there is nothing to compute let's return
    if len(records) == 0:
        return []

    # Format data for easy computation (one cell per path, with all values).
    paths = with_null_markers(records_projection)
    flatten_records = flatten(records, paths)

    final_projection = with_null_markers(desired_projections)
    for path in final_projection:
        await queue_field(ctx, collection, path, paths, flatten_records)

    return unflatten([flatten_records[paths.index(path)] for path in final_projection], Projection(*final_projection))
