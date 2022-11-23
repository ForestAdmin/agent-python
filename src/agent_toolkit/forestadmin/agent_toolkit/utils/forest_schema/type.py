import enum
import sys

if sys.version_info >= (3, 8):
    from typing import Literal, TypedDict
else:
    from typing_extensions import Literal, TypedDict

from typing import Any, List, Optional, Union

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias
from typing_extensions import NotRequired


class ValidationType(enum.Enum):
    PRESENT = "is present"
    GREATER_THAN = "is greater than"
    LESS_THAN = "is less than"
    BEFORE = "is before"
    AFTER = "is after"
    LONGER_THAN = "is longer than"
    SHORTER_THAN = "is shorter than"
    CONTAINS = "contains"
    LIKE = "is like"


class ServerValidationType(TypedDict):
    type: ValidationType
    value: Optional[Any]
    message: Optional[Any]


LiteralHasOne = Literal["HasOne"]
LiteralHasMany = Literal["HasMany"]
LiteralBelongsTo = Literal["BelongsTo"]
LiteralBelongsToMany = Literal["BelongsToMany"]

RelationServer = Union[LiteralHasOne, LiteralHasMany, LiteralBelongsTo, LiteralBelongsToMany]


class ForestServerField(TypedDict, total=False):
    field: str
    type: ColumnAlias
    defaultValue: Any
    enums: Optional[List[str]]
    integration: None
    isFilterable: bool
    isPrimaryKey: bool
    isReadOnly: bool
    isRequired: bool
    isSortable: bool
    isVirtual: bool
    reference: Optional[str]
    inverseOf: Optional[str]
    relationship: RelationServer
    validations: List[ServerValidationType]


LiteralPage = Literal["page"]


class ForestServerCollection(TypedDict):
    name: str
    icon: None
    integration: None
    isReadOnly: bool
    isSearchable: bool
    isVirtual: bool
    onlyForRelationships: bool
    paginationType: LiteralPage
    actions: NotRequired[List[Any]]
    fields: List[ForestServerField]
    segments: NotRequired[List[Any]]


class ForestServerActionHooks(TypedDict):
    load: bool
    change: List[Any]


class ForestServerActionField(TypedDict):
    value: Any
    defaultValue: Any
    description: Optional[str]
    enums: Optional[List[str]]
    field: str
    hook: Optional[str]
    isReadOnly: bool
    isRequired: bool
    reference: Optional[str]
    type: Union[ColumnAlias, Literal["File"]]
    widget: Optional[Literal["belongsto select", "file picker"]]


class ForestServerAction(TypedDict):
    id: str
    name: str
    type: Literal["single", "bulk", "global"]
    baseUrl: Optional[str]
    endpoint: str
    httpMethod: Literal["POST"]
    redirect: Any
    download: bool
    fields: List[ForestServerActionField]
    hooks: ForestServerActionHooks


"""
export type ForestServerSegment = {
  id: string;
  name: string;
};
"""


class ForestServerSegment(TypedDict):
    id: str
    name: str
