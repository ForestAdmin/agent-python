import json
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.resources.collections.requests import RequestCollection, RequestRelationCollection
from forestadmin.agent_toolkit.utils.context import Request
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection, CollectionException
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.interfaces.fields import (
    Column,
    ColumnAlias,
    Operator,
    PrimitiveType,
    is_column,
    is_polymorphic_many_to_one,
)
from forestadmin.datasource_toolkit.interfaces.models.collections import CollectionSchema
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
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.datasource_toolkit.validations.condition_tree import ConditionTreeValidator
from forestadmin.datasource_toolkit.validations.projection import ProjectionValidator

DEFAULT_ITEMS_PER_PAGE = 15
DEFAULT_PAGE_TO_SKIP = 1

STRING_TO_BOOLEAN = {
    "true": True,
    "yes": True,
    "1": True,
    "false": False,
    "no": False,
    "0": False,
}


class FilterException(AgentToolkitException):
    pass


def _get_collection(
    request: Union[RequestCollection, RequestRelationCollection]
) -> Union[CollectionCustomizer, Collection]:
    collection = request.collection
    if isinstance(request, RequestRelationCollection):
        collection = request.foreign_collection
    return collection


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


def parse_selection_ids(schema: CollectionSchema, request: RequestCollection) -> Tuple[List[CompositeIdAlias], bool]:
    if request.body:
        try:
            attributes: Dict[str, Any] = request.body.get("data", {}).get("attributes", {})  # type: ignore
        except AttributeError:
            attributes = {}
        exclude_ids = bool(attributes.get("all_records", False))  # type: ignore

        if exclude_ids is True:
            ids = [unpack_id(schema, pk) for pk in attributes.get("all_records_ids_excluded", [])]
        else:
            if "ids" in attributes:
                ids = [unpack_id(schema, pk) for pk in attributes["ids"]]
            elif isinstance(request.body.get("data"), list):
                ids = [unpack_id(schema, pk["id"]) for pk in request.body["data"]]
            else:
                ids = []
        return ids, exclude_ids

    raise Exception()


def parse_sort(request: Union[RequestCollection, RequestRelationCollection]):
    raw_sort_string: Optional[str] = _subset_or_query(request, "sort")
    if not raw_sort_string:
        return SortFactory.by_primary_keys(_get_collection(request))

    sort_list = []
    for sort_string in raw_sort_string.split(","):
        sort_field = sort_string.replace(".", ":")
        is_descending = sort_string[0] == "-"
        if is_descending:
            sort_field = sort_field[1:]
        sort_list.append({"field": sort_field, "ascending": not is_descending})
    return Sort(sort_list)


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
        if "page[size]" in request.query:
            items_per_page = int(request.query["page[size]"])
        if "page[number]" in request.query:
            page_to_skip = int(request.query["page[number]"])

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
    elif filters is None:
        filters: Optional[str] = _subset_or_query(request, "filter")
        if not filters and request.body and "filter" in request.body:
            filters = request.body["filter"]

    if not filters:
        return None

    json_filters = json.loads(filters) if isinstance(filters, str) else filters
    try:
        collection = _get_collection(request)
        json_filters = sanitize_json_filter(json_filters, collection)

        condition_tree = ConditionTreeFactory.from_plain_object(json_filters)
    except ConditionTreeFactoryException as e:
        raise FilterException(str(e))

    ConditionTreeValidator.validate(condition_tree, collection)

    return condition_tree


def sanitize_json_filter(jsoned_filters, collection):
    if "conditions" in jsoned_filters:
        for condition in jsoned_filters["conditions"]:
            condition = sanitize_json_filter(condition, collection)
        return jsoned_filters

    jsoned_filters["value"] = _parse_value(collection, jsoned_filters)
    return jsoned_filters


def _parse_value(collection: Collection, leaf: Dict[str, Any]):
    schema = cast(Column, CollectionUtils.get_field_schema(collection, leaf["field"]))
    expected_type = _get_expected_type_for_condition(Operator(leaf["operator"]), schema)

    return _cast_to_type(leaf["value"], expected_type)


def _cast_to_type(value: Any, expected_type: ColumnAlias) -> Any:
    if value is None:
        return value
    expected_type_to_cast: Dict[PrimitiveType, Callable[[Any], Any]] = {
        PrimitiveType.NUMBER: _parse_str_as_number,
        PrimitiveType.STRING: lambda value: f"{value}",
        PrimitiveType.DATE: lambda value: f"{value}",
        PrimitiveType.DATE_ONLY: lambda value: f"{value}",
        PrimitiveType.BOOLEAN: lambda value: (
            STRING_TO_BOOLEAN[value.lower()] if isinstance(value, str) else not not value
        ),
    }

    return_value = value
    if isinstance(expected_type, list):
        return_value = [v.strip() for v in value.split(",")] if isinstance(value, str) else value
        return_value = [
            _cast_to_type(item, expected_type[0])
            for item in return_value
            if not (expected_type[0] == PrimitiveType.NUMBER and not _is_str_a_number(item))
        ]
    elif expected_type in expected_type_to_cast.keys():
        method = expected_type_to_cast[expected_type]  # type:ignore
        return_value = method(value)
    return return_value


def _parse_str_as_number(value: Union[str, int, float]) -> Union[int, float]:
    if isinstance(value, int) or isinstance(value, float):
        return value
    try:
        return int(value)
    except Exception:
        return float(value)


def _is_str_a_number(value: Union[str, int, float]) -> bool:
    try:
        _parse_str_as_number(value)
        return True
    except Exception:
        return False


def _get_expected_type_for_condition(
    operator: Operator,
    field_schema: Column,
) -> PrimitiveType:
    operators_expecting_number = [
        Operator.SHORTER_THAN,
        Operator.LONGER_THAN,
        Operator.AFTER_X_HOURS_AGO,
        Operator.BEFORE_X_HOURS_AGO,
        Operator.PREVIOUS_X_DAYS,
        Operator.PREVIOUS_X_DAYS_TO_DATE,
    ]

    if operator in operators_expecting_number:
        return PrimitiveType.NUMBER

    if operator == Operator.IN:
        return [cast(PrimitiveType, field_schema["column_type"])]  # type:ignore

    return cast(PrimitiveType, field_schema["column_type"])


def parse_projection(request: Union[RequestCollection, RequestRelationCollection]) -> Projection:
    collection = _get_collection(request)
    schema = collection.schema
    if not request.query or not request.query.get(f"fields[{collection.name}]"):
        return ProjectionFactory.all(collection)

    root_fields = request.query[f"fields[{collection.name}]"].split(",")
    explicit_request = []
    for _field in root_fields:
        if not schema["fields"].get(_field):
            raise CollectionException(f"Field not found '{collection.name}.{_field}'")

        if is_column(schema["fields"][_field]):
            explicit_request.append(_field)
        elif is_polymorphic_many_to_one(schema["fields"][_field]):
            explicit_request.append(f"{_field}:*")
        else:
            query_params = f"fields[{_field}]"
            explicit_request.append(f"{_field}:{request.query[query_params]}")

    ProjectionValidator.validate(_get_collection(request), explicit_request)
    return Projection(*explicit_request)


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
