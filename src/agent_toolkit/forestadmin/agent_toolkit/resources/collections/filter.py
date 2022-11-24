import sys

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestRelationCollection
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.decorators.collections import CustomizedCollection
from forestadmin.datasource_toolkit.interfaces.fields import is_column, is_many_to_one, is_one_to_one
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import (
    ConditionTreeFactory,
    ConditionTreeFactoryException,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter, FilterComponent
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.projections.factory import ProjectionFactory
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from forestadmin.datasource_toolkit.interfaces.query.sort.factory import SortFactory
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.validations.condition_tree import (
    ConditionTreeValidator,
    ConditionTreeValidatorException,
)
from forestadmin.datasource_toolkit.validations.projection import ProjectionValidator

DEFAULT_ITEMS_PER_PAGE = 15
DEFAULT_PAGE_TO_SKIP = 1


class FilterException(AgentToolkitException):
    pass


def _all_records_subset_query(request: Request) -> Dict[str, Any]:
    try:
        return request.body.get("data", {}).get("attributes", {}).get("all_records_subset_query", {})  # type: ignore
    except AttributeError:
        # data may be a list
        return {}


def _subset_or_query(request: Request, key: str) -> Optional[str]:
    res = None
    if request.body:
        sub_res = _all_records_subset_query(request).get(key)
        if sub_res:
            res = str(sub_res)
    if not res and request.query:
        res = request.query.get(key)
        if res:
            res = str(res)
    return res


def parse_selection_ids(request: Request) -> Tuple[List[CompositeIdAlias], bool]:
    if request.body:
        try:
            attributes: Dict[str, Any] = request.body.get("data", {}).get("attributes", {})  # type: ignore
        except AttributeError:
            attributes = {}
        exclude_ids = bool(attributes.get("all_records", False))  # type: ignore
        if "ids" in attributes:
            ids = [[id] for id in attributes["ids"]]
        elif isinstance(request.body.get("data"), list):
            ids = [[r["id"]] for r in request.body["data"]]
        else:
            ids = []
        return ids, exclude_ids

    raise Exception()


def _get_collection(
    request: Union[RequestCollection, RequestRelationCollection]
) -> Union[CustomizedCollection, Collection]:
    collection = request.collection
    if isinstance(request, RequestRelationCollection):
        collection = request.foreign_collection
    return collection


def parse_sort(request: Union[RequestCollection, RequestRelationCollection]):
    sort_string: Optional[str] = _subset_or_query(request, "sort")
    if not sort_string:
        return SortFactory.by_primary_keys(_get_collection(request))

    sort_field = sort_string
    is_descending = sort_string[0] == "-"
    if is_descending:
        sort_field = sort_string[1:]
    return Sort([{"field": sort_field, "ascending": not is_descending}])


def parse_page(request: Request) -> Page:
    items_per_page: Optional[int] = None
    page_to_skip: Optional[int] = None
    if request.body:
        subset_query = _all_records_subset_query(request)
        if "page[size]" in subset_query:
            items_per_page = subset_query["page[size]"]
        if "page[number]" in subset_query:
            page_to_skip = subset_query["page[number]"]

    if not items_per_page and not page_to_skip and request.query:
        page: Dict[str, Any] = request.query.get("page", {})
        if "size" in page:
            items_per_page = page["size"]
        if "number" in page:
            page_to_skip = page["number"]

    if not items_per_page:
        items_per_page = DEFAULT_ITEMS_PER_PAGE
    if not page_to_skip:
        page_to_skip = DEFAULT_PAGE_TO_SKIP

    if (
        not isinstance(items_per_page, int)  # type: ignore
        or not isinstance(page_to_skip, int)  # type: ignore
        or page_to_skip <= 0  # type: ignore
        or items_per_page <= 0
    ):
        raise FilterException(f"Invalid pagination [limit: {items_per_page}, skip: {page_to_skip}]")

    return Page((page_to_skip - 1) * items_per_page, items_per_page)


def parse_search(request: Union[RequestCollection, RequestRelationCollection]):
    search: Optional[str] = _subset_or_query(request, "search")
    if search and not _get_collection(request).schema["searchable"]:
        raise FilterException("Collection is not searchable")

    return search


def parse_search_extended(request: Request) -> bool:
    extended: Optional[str] = _subset_or_query(request, "searchExtended")
    return extended is not None and extended not in ["0", "false"]


def parse_segment(request: Union[RequestCollection, RequestRelationCollection]) -> Optional[str]:
    segment: Optional[str] = _subset_or_query(request, "segment")
    if segment and segment not in _get_collection(request).schema["segments"]:
        raise FilterException(f"Invalid segment {segment}")
    return segment


def parse_timezone(request: Request) -> zoneinfo.ZoneInfo:
    if not request.query or "timezone" not in request.query:
        raise FilterException("Missing timezone")

    tz = request.query["timezone"]
    try:
        return zoneinfo.ZoneInfo(tz)
    except zoneinfo.ZoneInfoNotFoundError:
        raise FilterException(f"Invalid timezone {tz}")


def parse_condition_tree(request: Union[RequestCollection, RequestRelationCollection]) -> Optional[ConditionTree]:
    filters: Optional[str] = _subset_or_query(request, "filters")
    if not filters and request.body and "filters" in request.body:
        filters = request.body["filters"]
    if not filters:
        return None

    jsoned_filters = json.loads(filters)
    try:
        condition_tree = ConditionTreeFactory.from_plain_object(jsoned_filters)
    except ConditionTreeFactoryException as e:
        raise FilterException(str(e))

    try:
        ConditionTreeValidator.validate(condition_tree, _get_collection(request))
    except ConditionTreeValidatorException as e:
        raise FilterException(str(e))

    return condition_tree


def _parse_projection_fields(
    query: Dict[str, Any],
    collection: Union[CustomizedCollection, Collection],
    front_collection_name: str,
    is_related: bool = False,
) -> List[str]:
    projection_fields: List[str] = []
    try:
        fields: str = query[f"fields[{front_collection_name}]"]
    except KeyError:
        return ProjectionFactory.all(collection)

    if fields == "":
        return ProjectionFactory.all(collection)
    for field_name in fields.split(","):
        field_schema = collection.get_field(field_name)
        if is_column(field_schema):
            if is_related:
                projection_fields.append(f"{front_collection_name}:{field_name}")
            else:
                projection_fields.append(field_name)
        elif is_one_to_one(field_schema) or is_many_to_one(field_schema):
            fk_collection = collection.datasource.get_collection(field_schema["foreign_collection"])
            projection_fields.extend(_parse_projection_fields(query, fk_collection, field_name, True))
    return projection_fields


def parse_projection(request: Union[RequestCollection, RequestRelationCollection]):
    collection = _get_collection(request)
    if not request.query:
        return ProjectionFactory.all(collection)

    projection_fields = _parse_projection_fields(request.query, collection, collection.name)
    ProjectionValidator.validate(_get_collection(request), projection_fields)
    return Projection(*projection_fields)


def parse_projection_with_pks(request: Union[RequestCollection, RequestRelationCollection]):
    projection = parse_projection(request)
    return projection.with_pks(_get_collection(request))


def build_paginated_filter(
    request: Union[RequestCollection, RequestRelationCollection], scope: Optional[ConditionTree]
) -> PaginatedFilter:
    _filter = build_filter(request, scope)
    res = PaginatedFilter(
        {"sort": parse_sort(request), "page": parse_page(request), **_filter.to_filter_component()}  # type: ignore
    )
    return res


def build_filter(request: Union[RequestCollection, RequestRelationCollection], scope: Optional[ConditionTree]):
    filter_component: FilterComponent = {
        "search": parse_search(request),
        "search_extended": parse_search_extended(request),
        "timezone": parse_timezone(request),
    }
    segment = parse_segment(request)
    if segment:
        filter_component["segment"] = segment

    trees: List[ConditionTree] = []
    if scope:
        trees.append(scope)
    condition_tree = parse_condition_tree(request)
    if condition_tree:
        trees.append(condition_tree)

    if trees:
        filter_component["condition_tree"] = ConditionTreeFactory.intersect(trees)

    return Filter(filter_component)
