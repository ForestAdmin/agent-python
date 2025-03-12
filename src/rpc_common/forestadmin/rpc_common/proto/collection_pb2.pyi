from google.protobuf import any_pb2 as _any_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from forestadmin.rpc_common.proto import forest_pb2 as _forest_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CollectionChartRequest(_message.Message):
    __slots__ = ("caller", "ChartName", "RecordId")
    CALLER_FIELD_NUMBER: _ClassVar[int]
    CHARTNAME_FIELD_NUMBER: _ClassVar[int]
    RECORDID_FIELD_NUMBER: _ClassVar[int]
    caller: _forest_pb2.Caller
    ChartName: str
    RecordId: _any_pb2.Any
    def __init__(self, caller: _Optional[_Union[_forest_pb2.Caller, _Mapping]] = ..., ChartName: _Optional[str] = ..., RecordId: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...

class CreateRequest(_message.Message):
    __slots__ = ("Caller", "RecordData")
    CALLER_FIELD_NUMBER: _ClassVar[int]
    RECORDDATA_FIELD_NUMBER: _ClassVar[int]
    Caller: _forest_pb2.Caller
    RecordData: _containers.RepeatedCompositeFieldContainer[_struct_pb2.Struct]
    def __init__(self, Caller: _Optional[_Union[_forest_pb2.Caller, _Mapping]] = ..., RecordData: _Optional[_Iterable[_Union[_struct_pb2.Struct, _Mapping]]] = ...) -> None: ...
