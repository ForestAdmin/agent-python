import json
from collections.abc import Iterable
from hashlib import sha1
from typing import Any, Dict

from forestadmin.datasource_toolkit.interfaces.query.condition_tree.factory import ConditionTreeFactory
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import ConditionTree

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
