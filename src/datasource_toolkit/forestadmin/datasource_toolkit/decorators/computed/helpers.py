import copy
from typing import Any, Dict, List, Optional, Tuple, cast

from forestadmin.datasource_toolkit.context.collection_context import CollectionCustomizationContext
from forestadmin.datasource_toolkit.decorators.computed.exceptions import ComputedMixinException
from forestadmin.datasource_toolkit.decorators.computed.types import ComputedDefinition
from forestadmin.datasource_toolkit.decorators.computed.utils import Output, flatten, transform_unique_values, unflatten
from forestadmin.datasource_toolkit.interfaces.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import RelationAlias
from forestadmin.datasource_toolkit.interfaces.query.aggregation import (
    AggregateResult,
    Aggregation,
    PlainAggregationGroup,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias


def rewrite_fields(collection: Any, path: str) -> Projection:
    if ":" in path:
        prefix = path.split(":")[0]
        schema = cast(RelationAlias, collection.get_field(prefix))
        association = collection.datasource.get_collection(schema["foreign_collection"])
        return Projection(path).unnest().replace(lambda sub_path: rewrite_fields(association, sub_path)).nest(prefix)
    try:
        computed = collection.get_computed(path)
    except ComputedMixinException:
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
        return await computed["get_values"](unique_partials, context)

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
            dependencies = cast(List[str], dependencies.nest(new_path.split(":")[0])).sort()

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


def computed_aggregation_projection(
    collection: Collection,
    aggregation: Aggregation,
):
    plain_aggregation = aggregation._to_plain  # type: ignore
    if plain_aggregation.get("field"):
        plain_aggregation["field"] = rewrite_fields(collection, plain_aggregation["field"])  # type: ignore

    new_to_old_group: Dict[str, str] = {}
    groups: List[PlainAggregationGroup] = []
    for group in plain_aggregation.get("groups", []):
        new: str = rewrite_fields(collection, group["field"])[0]
        new_to_old_group[new] = group["field"]  # type: ignore
        group["field"] = new
        groups.append(group)
    plain_aggregation["groups"] = groups
    return Aggregation(plain_aggregation), new_to_old_group


def compute_aggregate_from_records(
    records: List[AggregateResult], new_to_old_group: Dict[str, str]
) -> List[AggregateResult]:
    for record in records:
        key, value = next(iter(record["group"].items()))
        record["group"] = {f"{new_to_old_group[key]}": value}
    return records
