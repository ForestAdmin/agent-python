from typing import Any, Dict, List, Literal, Optional

from forestadmin.agent_toolkit.utils.forest_schema.type import (
    AgentStackMeta,
    ForestServerSegment,
    ServerValidationType,
    WidgetEditConfiguration,
)
from forestadmin.datasource_toolkit.interfaces.actions import ActionFieldType
from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from typing_extensions import NotRequired, TypedDict


class SchemaV2Relation(TypedDict):
    name: str
    type: Literal["ManyToMany", "ManyToOne", "OneToOne", "OneToMany"]
    foreignCollection: str

    throughCollection: NotRequired[str]
    foreignKey: NotRequired[str]
    foreignKeyTarget: NotRequired[str]
    originKey: NotRequired[str]
    originKeyTarget: NotRequired[str]


class SchemaV2Field(TypedDict):
    name: str
    type: ColumnAlias
    isPrimaryKey: NotRequired[bool]
    filterOperators: List[str]
    enumerations: NotRequired[Optional[List[str]]]

    isWritable: NotRequired[bool]
    isSortable: NotRequired[bool]

    prefillFormValue: NotRequired[Optional[Any]]
    validations: NotRequired[List[ServerValidationType]]


class SchemaV2ActionField(TypedDict):
    name: str
    type: ActionFieldType
    description: NotRequired[Optional[str]]

    value: NotRequired[Optional[Any]]
    prefillValue: NotRequired[Optional[Any]]
    enumeration: NotRequired[Optional[List[str]]]
    isReadOnly: NotRequired[bool]
    isRequired: NotRequired[bool]
    reference: NotRequired[Optional[str]]
    widget: NotRequired[Optional[WidgetEditConfiguration]]


class SchemaV2Action(TypedDict):
    id: str
    name: str
    scope: Literal["single", "bulk", "global"]
    endpoint: str  # should it include the 'prefix' setting of the agent ??
    fields: NotRequired[List[SchemaV2ActionField]]
    download: NotRequired[bool]
    isDynamicForm: NotRequired[bool]


class SchemaV2Collection(TypedDict):
    name: str
    fields: List[SchemaV2Field]
    relations: List[SchemaV2Relation]

    segments: NotRequired[List[ForestServerSegment]]
    actions: NotRequired[List[SchemaV2Action]]

    canList: NotRequired[bool]
    canCreate: NotRequired[bool]
    canUpdate: NotRequired[bool]
    canDelete: NotRequired[bool]

    canCount: NotRequired[bool]
    canChart: NotRequired[bool]
    canSearch: NotRequired[bool]
    canNativeQuery: NotRequired[bool]


class AgentMetaV2(TypedDict):
    agent: str
    agent_version: str
    stack: AgentStackMeta
    datasources: NotRequired[
        List[Dict[str, Any]]
    ]  # here to store "name", "version", "dialect", ... and other nice to have values without formal keys


class ForestSchemaV2(TypedDict):
    collections: List[SchemaV2Collection]
    meta: AgentMetaV2


# MASKS
SCHEMA_V2_FIELDS_MASK = {
    "enumerations": None,
    "isPrimaryKey": False,
    "prefillFormValue": None,
    "isSortable": True,
    "isWritable": True,
    "validations": [],
}

SCHEMA_V2_ACTION_FIELD_MASK = {
    "value": None,
    "prefillValue": None,
    "enumeration": None,
    "description": "",
    "isReadOnly": False,
    "isRequired": False,
    "reference": None,
    "widget": None,
}

SCHEMA_V2_ACTION_MASK = {
    "download": False,
    "isDynamicForm": False,
    "fields": [],
}

SCHEMA_V2_COLLECTION_MASK = {
    "segments": [],
    "actions": [],
    "fields": [],  # I don't kow if we can have a collection without fields
    "relations": [],  # I don't kow if we can have a collection without relations
    "canList": True,
    "canCreate": True,
    "canUpdate": True,
    "canDelete": True,
    "canCount": True,
    "canSearch": True,
    "canChart": True,
    "canNativeQuery": True,
}


# reduce templates
def template_reduce_collection(collection: SchemaV2Collection) -> SchemaV2Collection:
    fields: List[SchemaV2Field] = collection.get("fields", [])
    relations: List[SchemaV2Relation] = collection.get("relations", [])
    actions: List[SchemaV2Action] = collection.get("actions", [])

    reduced: SchemaV2Collection = {**collection}
    reduced["fields"] = [template_reduce_field(field) for field in fields]
    reduced["relations"] = relations
    reduced["actions"] = [template_reduce_action(action) for action in actions]
    return _reduce_from_template(reduced, SCHEMA_V2_COLLECTION_MASK)  # type:ignore


def template_reduce_field(collection: SchemaV2Field) -> SchemaV2Field:
    return _reduce_from_template(collection, SCHEMA_V2_FIELDS_MASK)  # type:ignore


def template_reduce_action(action: SchemaV2Action) -> SchemaV2Action:
    fields: List[SchemaV2ActionField] = action.get("fields", [])
    reduced_action: SchemaV2Action = {**action}
    reduced_action["fields"] = [template_reduce_action_field(action) for action in fields]
    return _reduce_from_template(reduced_action, SCHEMA_V2_ACTION_MASK)  # type:ignore


def template_reduce_action_field(action_field: SchemaV2ActionField) -> SchemaV2ActionField:
    reduced: SchemaV2ActionField = _reduce_from_template(action_field, SCHEMA_V2_ACTION_FIELD_MASK)  # type:ignore
    return reduced


def _reduce_from_template(input, mask):
    # reduced = {}
    # for key, value in input.items():
    #     if key not in mask or input[key] != mask[key]:
    #         reduced[key] = value
    reduced = {**input}
    for key, value in mask.items():
        if key in input and input[key] == value:
            del reduced[key]
    return reduced


# apply templates
def template_apply_collection(collection: SchemaV2Collection) -> SchemaV2Collection:
    fields: List[SchemaV2Field] = collection.get("fields", [])
    actions: List[SchemaV2Action] = collection.get("actions", [])

    full: SchemaV2Collection = {**collection}
    full["fields"] = [template_apply_field(field) for field in fields]
    full["actions"] = [template_apply_action(action) for action in actions]
    return _apply_from_template(collection, SCHEMA_V2_COLLECTION_MASK)  # type:ignore


def template_apply_field(collection: SchemaV2Field) -> SchemaV2Field:
    return _apply_from_template(collection, SCHEMA_V2_FIELDS_MASK)  # type:ignore


def template_apply_action(action: SchemaV2Action) -> SchemaV2Action:
    fields = action.get("fields", [])
    full: SchemaV2Action = {**action}

    full["fields"] = [template_apply_action_field(field) for field in fields]
    return _apply_from_template(full, SCHEMA_V2_ACTION_MASK)  # type:ignore


def template_apply_action_field(action_field: SchemaV2ActionField) -> SchemaV2ActionField:
    return _apply_from_template(action_field, SCHEMA_V2_ACTION_FIELD_MASK)  # type:ignore


def _apply_from_template(input, mask):
    full = {}
    for key, value in mask.items():
        full[key] = value
    for key, value in input.items():
        full[key] = value
    return full
