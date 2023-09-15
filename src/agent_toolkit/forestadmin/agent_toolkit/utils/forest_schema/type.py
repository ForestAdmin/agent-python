import enum
from typing import Any, List, Literal, Optional, TypedDict, Union

from forestadmin.datasource_toolkit.interfaces.fields import ColumnAlias


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


class AgentStackMeta(TypedDict, total=False):
    engine: Literal["python"]
    engine_version: str
    database_type: str
    orm_version: str


class AgentMeta(TypedDict):
    liana: str
    liana_version: str
    stack: AgentStackMeta
    schemaFileHash: str


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


class ForestServerSegment(TypedDict):
    id: str
    name: str


class ForestServerCollection(TypedDict):
    name: str
    icon: None
    integration: None
    isReadOnly: bool
    isSearchable: bool
    isVirtual: bool
    onlyForRelationships: bool
    paginationType: LiteralPage
    actions: Optional[List[ForestServerAction]]
    fields: List[ForestServerField]
    segments: Optional[List[ForestServerSegment]]


class ForestSchema(TypedDict):
    data: List[ForestServerCollection]
    meta: AgentMeta
