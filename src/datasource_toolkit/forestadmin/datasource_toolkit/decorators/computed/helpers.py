import copy
from typing import Any, Awaitable, List, Optional, Tuple, cast

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.computed.utils import Output, flatten, transform_unique_values, unflatten
from forestadmin.datasource_toolkit.interfaces.fields import RelationAlias
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def rewrite_fields(collection: Any, path: str) -> Projection:
    if ":" in path:
        prefix = path.split(":")[0]
        schema = cast(RelationAlias, collection.get_field(prefix))
        association = collection.datasource.get_collection(schema["foreign_collection"])
        return Projection(path).unnest().replace(lambda sub_path: rewrite_fields(association, sub_path)).nest(prefix)

    computed = collection.get_computed(path)
    if computed is None:
        return Projection(path)
    else:
        return Projection(*computed["dependencies"]).replace(lambda dep_path: rewrite_fields(collection, dep_path))


async def compute_field(
    context: CollectionCustomizationContext,
    computed: ComputedDefinition,
    paths: List[str],
    dependency_values: List[List[Any]],
) -> List[Output]:
    async def _compute_field_cb(unique_partials: List[RecordsDataAlias]) -> Output:
        ret = computed["get_values"](unique_partials, context)
        if isinstance(ret, Awaitable):
            ret = await ret
        return ret

    return await transform_unique_values(unflatten(dependency_values, Projection(*paths)), _compute_field_cb)


async def queue_field(
    ctx: CollectionCustomizationContext,
    collection: Any,
    new_path: str,
    paths: List[str],
    flatten_records: List[List[Any]],
):
    if new_path not in paths:
        computed = collection.get_computed(new_path)
        dependencies = Projection(*computed["dependencies"])
        if ":" in new_path:
            nested_field = new_path.split(":")[0]
            dependencies = cast(List[str], dependencies.nest(nested_field))
            dependencies.sort()
        for path in cast(List[str], dependencies):
            await queue_field(ctx, collection, path, paths, flatten_records.copy())
        dependency_values = [flatten_records[paths.index(path)] for path in cast(List[str], dependencies)]
        paths.append(new_path)

        return await compute_field(ctx, computed, computed["dependencies"], copy.deepcopy(dependency_values)) or []


async def compute_from_records(
    ctx: CollectionCustomizationContext,
    collection: Any,
    records_projection: Projection,
    desired_projections: Projection,
    records: List[Optional[RecordsDataAlias]],
) -> List[RecordsDataAlias]:
    paths: List[str] = [*records_projection]
    paths.sort()
    cast(List[str], desired_projections).sort()
    flatten_records = flatten(records, paths)
    add_operations: List[Tuple[int, Any]] = []
    delete_operations: List[int] = []

    for i, path in enumerate(cast(List[str], desired_projections)):
        value = await queue_field(ctx, collection, path, paths, copy.deepcopy(flatten_records))
        if value is not None:
            add_operations.append((i, value))
            # operations.append((i, value, 1))

    for path in paths:
        if path not in desired_projections:
            delete_operations.append(paths.index(path))

    delete_operations.sort(key=lambda o: o, reverse=True)
    add_operations.sort(key=lambda o: o[0])
    for i in delete_operations:
        del flatten_records[i]

    for i, value in add_operations:
        flatten_records.insert(i, value)

    return [u for u in unflatten(flatten_records, desired_projections) if u]
