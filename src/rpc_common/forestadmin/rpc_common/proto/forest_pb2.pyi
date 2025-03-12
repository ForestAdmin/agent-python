from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Caller(_message.Message):
    __slots__ = ("RendererId", "UserId", "Tags", "Email", "FirstName", "LastName", "Team", "Timezone")
    class TagsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class Request(_message.Message):
        __slots__ = ("Ip",)
        IP_FIELD_NUMBER: _ClassVar[int]
        Ip: str
        def __init__(self, Ip: _Optional[str] = ...) -> None: ...
    RENDERERID_FIELD_NUMBER: _ClassVar[int]
    USERID_FIELD_NUMBER: _ClassVar[int]
    TAGS_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FIRSTNAME_FIELD_NUMBER: _ClassVar[int]
    LASTNAME_FIELD_NUMBER: _ClassVar[int]
    TEAM_FIELD_NUMBER: _ClassVar[int]
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    RendererId: int
    UserId: int
    Tags: _containers.ScalarMap[str, str]
    Email: str
    FirstName: str
    LastName: str
    Team: str
    Timezone: str
    def __init__(self, RendererId: _Optional[int] = ..., UserId: _Optional[int] = ..., Tags: _Optional[_Mapping[str, str]] = ..., Email: _Optional[str] = ..., FirstName: _Optional[str] = ..., LastName: _Optional[str] = ..., Team: _Optional[str] = ..., Timezone: _Optional[str] = ...) -> None: ...

class DataSourceSchema(_message.Message):
    __slots__ = ("Charts", "ConnectionNames", "Collections")
    CHARTS_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONNAMES_FIELD_NUMBER: _ClassVar[int]
    COLLECTIONS_FIELD_NUMBER: _ClassVar[int]
    Charts: _containers.RepeatedScalarFieldContainer[str]
    ConnectionNames: _containers.RepeatedScalarFieldContainer[str]
    Collections: _containers.RepeatedCompositeFieldContainer[CollectionSchema]
    def __init__(self, Charts: _Optional[_Iterable[str]] = ..., ConnectionNames: _Optional[_Iterable[str]] = ..., Collections: _Optional[_Iterable[_Union[CollectionSchema, _Mapping]]] = ...) -> None: ...

class CollectionSchema(_message.Message):
    __slots__ = ("name", "actions", "fields", "charts", "searchable", "countable", "segments")
    class ActionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _struct_pb2.Struct
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    class FieldsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _struct_pb2.Struct
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    ACTIONS_FIELD_NUMBER: _ClassVar[int]
    FIELDS_FIELD_NUMBER: _ClassVar[int]
    CHARTS_FIELD_NUMBER: _ClassVar[int]
    SEARCHABLE_FIELD_NUMBER: _ClassVar[int]
    COUNTABLE_FIELD_NUMBER: _ClassVar[int]
    SEGMENTS_FIELD_NUMBER: _ClassVar[int]
    name: str
    actions: _containers.MessageMap[str, _struct_pb2.Struct]
    fields: _containers.MessageMap[str, _struct_pb2.Struct]
    charts: _containers.RepeatedScalarFieldContainer[str]
    searchable: bool
    countable: bool
    segments: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, name: _Optional[str] = ..., actions: _Optional[_Mapping[str, _struct_pb2.Struct]] = ..., fields: _Optional[_Mapping[str, _struct_pb2.Struct]] = ..., charts: _Optional[_Iterable[str]] = ..., searchable: bool = ..., countable: bool = ..., segments: _Optional[_Iterable[str]] = ...) -> None: ...
