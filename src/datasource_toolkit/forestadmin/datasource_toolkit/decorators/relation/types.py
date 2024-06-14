from typing import Literal, Optional, Union

from forestadmin.datasource_toolkit.interfaces.fields import FieldType
from typing_extensions import NotRequired, TypedDict


class PartialManyToOne(TypedDict):
    foreign_collection: str
    foreign_key: str
    foreign_key_target: NotRequired[Optional[str]]
    type: Literal[FieldType.MANY_TO_ONE]


class PartialOneToOne(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: NotRequired[Optional[str]]
    type: Literal[FieldType.ONE_TO_ONE]


class PartialOneToMany(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: NotRequired[Optional[str]]
    type: Literal[FieldType.ONE_TO_MANY]


class PartialManyToMany(TypedDict):
    through_collection: str
    foreign_collection: str
    foreign_key: str
    foreign_key_target: NotRequired[Optional[str]]
    foreign_relation: NotRequired[Optional[str]]
    origin_key: str
    origin_key_target: NotRequired[Optional[str]]
    type: Literal[FieldType.MANY_TO_MANY]


RelationDefinition = Union[PartialManyToMany, PartialManyToOne, PartialOneToOne, PartialOneToMany]
