from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import any_pb2 as _any_pb2
from forestadmin.rpc_common.proto import forest_pb2 as _forest_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SchemaResponse(_message.Message):
    __slots__ = ("Schema", "Collections")
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    COLLECTIONS_FIELD_NUMBER: _ClassVar[int]
    Schema: _forest_pb2.DataSourceSchema
    Collections: _containers.RepeatedCompositeFieldContainer[_forest_pb2.CollectionSchema]
    def __init__(self, Schema: _Optional[_Union[_forest_pb2.DataSourceSchema, _Mapping]] = ..., Collections: _Optional[_Iterable[_Union[_forest_pb2.CollectionSchema, _Mapping]]] = ...) -> None: ...

class DatasourceChartRequest(_message.Message):
    __slots__ = ("caller", "ChartName")
    CALLER_FIELD_NUMBER: _ClassVar[int]
    CHARTNAME_FIELD_NUMBER: _ClassVar[int]
    caller: _forest_pb2.Caller
    ChartName: str
    def __init__(self, caller: _Optional[_Union[_forest_pb2.Caller, _Mapping]] = ..., ChartName: _Optional[str] = ...) -> None: ...

class NativeQueryRequest(_message.Message):
    __slots__ = ("Caller", "Query", "Parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _any_pb2.Any
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_any_pb2.Any, _Mapping]] = ...) -> None: ...
    CALLER_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    Caller: _forest_pb2.Caller
    Query: str
    Parameters: _containers.MessageMap[str, _any_pb2.Any]
    def __init__(self, Caller: _Optional[_Union[_forest_pb2.Caller, _Mapping]] = ..., Query: _Optional[str] = ..., Parameters: _Optional[_Mapping[str, _any_pb2.Any]] = ...) -> None: ...
