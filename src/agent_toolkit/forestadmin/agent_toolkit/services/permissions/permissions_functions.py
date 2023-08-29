import itertools
import json
from collections.abc import Iterable
from hashlib import sha1
from typing import Any, Dict, List, Set, Tuple, cast

from forestadmin.agent_toolkit.services.permissions.permissions_types import (
    PermissionBody,
    PermissionServiceException,
    Scope,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.branch import ConditionTreeBranch

##################
# Decode methods #
##################


def _decode_scope_permissions(raw_permission: Dict[Any, Any]) -> Dict[str, ConditionTree]:
    scopes = {}
    for collection_name, value in raw_permission.items():
        if value.get("scope") is not None:
            scopes[collection_name] = ConditionTreeFactory.from_plain_object(value["scope"])
    return scopes


def _decode_crud_permissions(collection: Dict[Any, Any]) -> Dict[str, Any]:
    return {
        "browse": collection["collection"]["browseEnabled"]["roles"],
        "read": collection["collection"]["readEnabled"]["roles"],
        "edit": collection["collection"]["editEnabled"]["roles"],
        "add": collection["collection"]["addEnabled"]["roles"],
        "delete": collection["collection"]["deleteEnabled"]["roles"],
        "export": collection["collection"]["exportEnabled"]["roles"],
    }


def _decode_actions_permissions(collection: Dict[Any, Any]) -> Dict[Any, Any]:
    actions = {"actions": {}}
    for id, action in collection["actions"].items():
        actions["actions"][id] = {
            "triggerEnabled": action["triggerEnabled"]["roles"],
            "triggerConditions": action["triggerConditions"],
            "approvalRequired": action["approvalRequired"]["roles"],
            "approvalRequiredConditions": action["approvalRequiredConditions"],
            "userApprovalEnabled": action["userApprovalEnabled"]["roles"],
            "userApprovalConditions": action["userApprovalConditions"],
            "selfApprovalEnabled": action["selfApprovalEnabled"]["roles"],
        }
    return actions


def decode_permission_body(rendering_id: int, body: Dict[str, Any]) -> PermissionBody:
    if not body["meta"].get("rolesACLActivated"):
        raise PermissionServiceException("Roles V2 are unsupported")

    collections: Dict[str, Any] = {}
    stats: Dict[str, Any] = body.get("stats", {})
    renderings: Dict[str, Any] = {}

    if "data" in body:
        if body["data"].get("collections"):
            collections = body["data"]["collections"]

        renderings = body["data"].get("renderings", {})
        if str(rendering_id) in renderings:
            renderings = renderings[str(rendering_id)]
    actions, actions_by_user = _decode_action_permissions(collections)
    actions.update(_decode_chart_permissions(stats))

    scopes = _decode_scopes(renderings)

    return {"actions": actions, "actions_by_user": actions_by_user, "scopes": scopes}


def _decode_scopes(rendering: Dict[str, Any]) -> Dict[str, Scope]:
    scopes: Dict[str, Scope] = {}
    for name, v in rendering.items():
        if v.get("scope"):
            scopes[name] = {
                **v["scope"],
                "condition_tree": cast(
                    ConditionTreeBranch, ConditionTreeFactory.from_plain_object(v["scope"]["filter"])
                ),
                "dynamic_scope_values": v["scope"]["dynamicScopesValues"].get("users", {}),
            }
    return scopes


def _decode_action_permissions(collections: Dict[str, Any]) -> Tuple[Set[str], Dict[str, Set[int]]]:
    actions: Set[str] = set()
    actions_by_user: Dict[str, Set[int]] = {}

    for name, settings in collections.items():
        for action_name, user_ids in settings.get("collection", {}).items():
            # Remove 'Enabled' from the name
            short_name = action_name[:-7]
            key = f"{short_name}:{name}"
            if isinstance(user_ids, bool):
                actions.add(key)
            else:
                actions_by_user[key] = set(user_ids)

        for action_name, perms in settings.get("actions", {}).items():
            user_ids = perms["triggerEnabled"]
            key = f"custom:{action_name}:{name}"
            if isinstance(user_ids, bool):
                actions.add(key)
            else:
                actions_by_user[key] = set(user_ids)

    return actions, actions_by_user


def _decode_chart_permissions(stats: Dict[str, Any]) -> List[str]:
    server_charts = list(itertools.chain(*stats.values()))
    hashes: List[str] = []
    for chart in server_charts:
        if isinstance(chart, str):  # Queries
            hashes.append(f"chart:{hash(chart)}")
        else:
            frontend_chart = {
                "type": chart.get("type"),
                "filters": chart.get("filter"),
                "aggregate": chart.get("aggregator"),
                "aggregate_field": chart.get("aggregateFieldName"),
                "collection": chart.get("sourceCollectionId"),
                "time_range": chart.get("timeRange"),
                "group_by_date_field": (chart.get("type") == "Line" and chart.get("groupByFieldName")) or None,
                "group_by_field": (chart.get("type") != "Line" and chart.get("groupByFieldName")) or None,
                "limit": chart.get("limit"),
                "label_field": chart.get("labelFieldName"),
                "relationship_field": chart.get("relationshipFieldName"),
            }
            h = hash(json.dumps(dict((k, v) for k, v in frontend_chart.items() if v is not None)))
            hashes.append(f"chart:{h}")
    return hashes


################
# Hash methods #
################


def _dict_hash(data: Dict[Any, Any]) -> str:
    sorted_data = _order_dict(data)
    return sha1(json.dumps(sorted_data).encode()).hexdigest()


def _hash_chart(chart: Dict[Any, Any]) -> str:
    known_chart_keys = [
        "type",
        "apiRoute",
        "smartRoute",
        "query",
        "labelFieldName",
        "filter",
        "sourceCollectionName",
        "aggregator",
        "aggregateFieldName",
        "groupByFieldName",
        "relationshipFieldName",
        "limit",
        "timeRange",
        "objective",
        "numeratorChartId",
        "denominatorChartId",
    ]
    dct = {
        k: v
        for k, v in chart.items()
        if k in known_chart_keys and v is not None and (not isinstance(v, Iterable) or len(v) > 0)
    }
    return _dict_hash(dct)


def _order_dict(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
    result = {}
    for key in sorted(dictionary.keys()):
        if isinstance(dictionary[key], dict):
            result[key] = _order_dict(dictionary[key])
        elif isinstance(dictionary[key], list):
            result[key] = []
            for i, _ in enumerate(dictionary[key]):
                result[key].append(_order_dict(dictionary[key][i]))
        else:
            result[key] = dictionary[key]
    return result
