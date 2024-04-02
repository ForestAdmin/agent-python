from typing import Any, List, Literal

from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerAction,
    ForestServerSegment,
    ServerValidationType,
)
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
    enumerations: NotRequired[List[str]]

    isWritable: NotRequired[bool]
    isSortable: NotRequired[bool]

    prefillFormValue: Any
    validations: NotRequired[List[ServerValidationType]]


class SchemaV2Collection(TypedDict):
    name: str
    fields: List[SchemaV2Field]  # to define
    relations: List  # to define

    segments: NotRequired[List[ForestServerSegment]]
    actions: NotRequired[List[ForestServerAction]]

    canList: NotRequired[bool]
    canCreate: NotRequired[bool]
    canUpdate: NotRequired[bool]
    canDelete: NotRequired[bool]

    canCount: NotRequired[bool]
    canChart: NotRequired[bool]
    canSearch: NotRequired[bool]
    canNativeQuery: NotRequired[bool]


# MASKS
SCHEMA_V2_FIELDS_MASK = {
    "enumerations": None,
    "isPrimaryKey": False,
    "isWritable": True,
    "prefillFormValue": None,
    "isSortable": True,
    "isWritable": True,
    "validations": [],
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


def template_reduce_field(collection: SchemaV2Field) -> SchemaV2Field:
    return _reduce_from_template(collection, SCHEMA_V2_FIELDS_MASK)  # type:ignore


def template_reduce_collection(collection: SchemaV2Collection) -> SchemaV2Collection:
    return _reduce_from_template(collection, SCHEMA_V2_COLLECTION_MASK)  # type:ignore


def template_apply_field(collection: SchemaV2Field) -> SchemaV2Field:
    return _apply_from_template(collection, SCHEMA_V2_FIELDS_MASK)  # type:ignore


def template_apply_collection(collection: SchemaV2Collection) -> SchemaV2Collection:
    return _apply_from_template(collection, SCHEMA_V2_COLLECTION_MASK)  # type:ignore


def _reduce_from_template(input, mask):
    reduced = {}
    for key, value in input.items():
        if key not in mask or input[key] != mask[key]:
            reduced[key] = value
    return reduced


def _apply_from_template(input, mask):
    full = {}
    for key, value in mask.items():
        full[key] = value
    for key, value in input.items():
        full[key] = value
    return full
