from typing import Any, Dict, List

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.leaf import ConditionTreeLeaf
from forestadmin.datasource_toolkit.interfaces.query.filter.paginated import PaginatedFilter
from forestadmin.datasource_toolkit.interfaces.query.filter.unpaginated import Filter
from forestadmin.datasource_toolkit.interfaces.query.page import Page
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.query.sort import Sort
from forestadmin.datasource_toolkit.utils.collections import CollectionUtils
from forestadmin.rpc_common.serializers.collection.record import RecordSerializer
from forestadmin.rpc_common.serializers.utils import OperatorSerializer, TimezoneSerializer, camel_to_snake_case


class ConditionTreeSerializer:
    @staticmethod
    def serialize(condition_tree: ConditionTree, collection: Collection) -> Dict:
        if isinstance(condition_tree, ConditionTreeBranch):
            return {
                "aggregator": condition_tree.aggregator.value,
                "conditions": [
                    ConditionTreeSerializer.serialize(condition, collection) for condition in condition_tree.conditions
                ],
            }
        elif isinstance(condition_tree, ConditionTreeLeaf):
            return {
                "operator": OperatorSerializer.serialize(condition_tree.operator),
                "field": condition_tree.field,
                "value": ConditionTreeSerializer._serialize_value(
                    condition_tree.value, collection, condition_tree.field
                ),
            }
        raise ValueError(f"Unknown condition tree type: {type(condition_tree)}")

    @staticmethod
    def _serialize_value(value: Any, collection: Collection, field_name: str) -> Any:
        if value is None:
            return None
        field_schema = CollectionUtils.get_field_schema(collection, field_name)  #  type:ignore
        type_ = field_schema["column_type"]

        if type_ == PrimitiveType.DATE:
            ret = value.isoformat()
        elif type_ == PrimitiveType.DATE_ONLY:
            ret = value.isoformat()
        elif type_ == PrimitiveType.DATE:
            ret = value.isoformat()
        elif type_ == PrimitiveType.POINT:
            ret = (value[0], value[1])
        elif type_ == PrimitiveType.UUID:
            ret = str(value)
        else:
            ret = value

        return ret

    @staticmethod
    def deserialize(condition_tree: Dict, collection: Collection) -> ConditionTree:
        if "aggregator" in condition_tree:
            return ConditionTreeBranch(
                aggregator=condition_tree["aggregator"],
                conditions=[
                    ConditionTreeSerializer.deserialize(condition, collection)
                    for condition in condition_tree["conditions"]
                ],
            )
        elif "operator" in condition_tree:
            return ConditionTreeLeaf(
                operator=camel_to_snake_case(condition_tree["operator"]),  # type:ignore
                field=condition_tree["field"],
                value=ConditionTreeSerializer._deserialize_value(
                    condition_tree.get("value"), collection, condition_tree["field"]
                ),
            )
        raise ValueError(f"Unknown condition tree type: {condition_tree.keys()}")

    @staticmethod
    def _deserialize_value(value: Any, collection: Collection, field_name: str) -> Any:
        if value is None:
            return None
        field_schema = CollectionUtils.get_field_schema(collection, field_name)  #  type:ignore
        return RecordSerializer._deserialize_primitive_type(field_schema["column_type"], value)  #  type:ignore


class FilterSerializer:
    @staticmethod
    def serialize(filter_: Filter, collection: Collection) -> Dict:
        return {
            "condition_tree": (
                ConditionTreeSerializer.serialize(filter_.condition_tree, collection)
                if filter_.condition_tree is not None
                else None
            ),
            "search": filter_.search,
            "search_extended": filter_.search_extended,
            "segment": filter_.segment,
            "timezone": TimezoneSerializer.serialize(filter_.timezone),
        }

    @staticmethod
    def deserialize(filter_: Dict, collection: Collection) -> Filter:
        return Filter(
            {
                "condition_tree": (
                    ConditionTreeSerializer.deserialize(filter_["condition_tree"], collection)
                    if filter_.get("condition_tree") is not None
                    else None
                ),  # type: ignore
                "search": filter_["search"],
                "search_extended": filter_["search_extended"],
                "segment": filter_["segment"],
                "timezone": TimezoneSerializer.deserialize(filter_["timezone"]),
            }
        )


class PaginatedFilterSerializer:
    @staticmethod
    def serialize(filter_: PaginatedFilter, collection: Collection) -> Dict:
        ret = FilterSerializer.serialize(filter_.to_base_filter(), collection)
        ret["sort"] = filter_.sort
        ret["page"] = {"skip": filter_.page.skip, "limit": filter_.page.limit} if filter_.page else None
        return ret

    @staticmethod
    def deserialize(serialized_filter: Dict, collection: Collection) -> PaginatedFilter:
        ret = FilterSerializer.deserialize(serialized_filter, collection)
        ret = PaginatedFilter.from_base_filter(ret)
        ret.sort = Sort(serialized_filter["sort"]) if serialized_filter.get("sort") is not None else None  # type: ignore
        ret.page = (
            Page(skip=serialized_filter["page"]["skip"], limit=serialized_filter["page"]["limit"])
            if serialized_filter.get("page") is not None
            else None
        )  #  type: ignore
        return ret


class ProjectionSerializer:
    @staticmethod
    def serialize(projection: Projection) -> List[str]:
        return [*projection]

    @staticmethod
    def deserialize(projection: List[str]) -> Projection:
        return Projection(*projection)
