from typing import Any, Awaitable, Callable, Generic, List, Optional, TypedDict, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType, File
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from typing_extensions import NotRequired

Context = TypeVar("Context", bound=ActionContext)
Result = TypeVar("Result")

ValueOrHandler = Union[Callable[[Context], Awaitable[Result]], Callable[[Context], Result], Result]


class PlainBaseDynamicField(TypedDict):
    label: str
    description: NotRequired[str]
    is_required: NotRequired[bool]
    is_read_only: NotRequired[bool]


class PlainField(PlainBaseDynamicField):
    type: ActionFieldType


class BaseDynamicField(Generic[Context, Result]):
    ATTR_TO_EVALUATE = ("is_required", "is_read_only", "if_", "value", "default_value")
    TYPE: ActionFieldType

    def __init__(
        self,
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[Context, bool]] = False,
        is_read_only: Optional[ValueOrHandler[Context, bool]] = False,
        if_: Optional[ValueOrHandler[Context, Any]] = None,
        value: Optional[ValueOrHandler[Context, Result]] = None,
        default_value: Optional[ValueOrHandler[Context, Result]] = None,
    ):
        self.label = label
        self.description = description
        self._is_required = is_required
        self._is_read_only = is_read_only
        self._if_ = if_
        self._value = value
        self._default_value = default_value

    @property
    def dynamic_fields(self):
        return [self._is_required, self._is_read_only, self._if_, self._value, self._default_value]

    @property
    def is_dynamic(self):
        return any(map(lambda x: isinstance(x, Callable), self.dynamic_fields))

    async def to_action_field(self, context: Context, default_value: Result) -> ActionField:
        return ActionField(
            type=self.TYPE,
            label=self.label,
            description=self.description,
            is_read_only=await self.is_read_only(context),
            is_required=await self.is_required(context),
            value=await self.value(context) or default_value,
            default_value=await self.default_value(context),
            collection_name=None,
            enum_values=None,
            watch_changes=False,
        )

    async def default_value(self, context: Context) -> Result:
        return await self._evaluate(context, self._default_value)

    async def is_required(self, context: Context) -> bool:
        return await self._evaluate(context, self._is_required)

    async def is_read_only(self, context: Context) -> bool:
        return await self._evaluate(context, self._is_read_only)

    async def if_(self, context: Context) -> Any:
        return self._if_ is None or await self._evaluate(context, self._if_)

    async def value(self, context: Context) -> Result:
        return await self._evaluate(context, self._value)

    async def _evaluate(self, context: Context, attribute: ValueOrHandler[ActionContext, Any]):
        if isinstance(attribute, Callable):
            res = attribute(context)
            if isinstance(res, Awaitable):
                return await res
            return res
        # ugly hack for static or classmethod in python<3.10
        # https://stackoverflow.com/questions/41921255/staticmethod-object-is-not-callable
        elif hasattr(attribute, "__func__") and isinstance(attribute.__func__, Callable):
            res = attribute.__func__(context)
            if isinstance(res, Awaitable):
                return await res
            return res
        else:
            return attribute

    # @classmethod
    # def from_plain_field(cls, plain_field: PlainBaseDynamicField) -> Self:
    #     return cls(**plain_field)


class PlainCollectionDynamicField(PlainField):
    collection_name: ValueOrHandler[ActionContext, str]
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, CompositeIdAlias]]
    default_value: NotRequired[ValueOrHandler[ActionContext, CompositeIdAlias]]


# collection
class CollectionDynamicField(Generic[Context], BaseDynamicField[Context, CompositeIdAlias]):
    TYPE = ActionFieldType.COLLECTION

    def __init__(
        self,
        collection_name: ValueOrHandler[Context, str],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[Context, bool]] = False,
        is_read_only: Optional[ValueOrHandler[Context, bool]] = False,
        if_: Optional[Awaitable[Any]] = None,
        value: Optional[ValueOrHandler[Context, CompositeIdAlias]] = None,
        default_value: Optional[ValueOrHandler[Context, CompositeIdAlias]] = None,
    ):
        super(CollectionDynamicField, self).__init__(
            label, description, is_required, is_read_only, if_, value, default_value
        )
        self._collection_name = collection_name

    @property
    def dynamic_fields(self):
        return [*super(CollectionDynamicField, self).dynamic_fields, self._collection_name]

    async def collection_name(self, context: Context) -> str:
        return await self._evaluate(context, self._collection_name)

    async def to_action_field(self, context: Context, default_value: CompositeIdAlias) -> ActionField:
        res = await super(CollectionDynamicField, self).to_action_field(context, default_value)
        res["collection_name"] = await self.collection_name(context)
        return res

    # @classmethod
    # def from_plain_field(  # type: ignore
    #     cls, plain_field: PlainCollectionDynamicField
    # ) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


# enum
class PlainEnumDynamicField(PlainField):
    enum_values: ValueOrHandler[ActionContext, List[str]]
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, str]]
    default_value: NotRequired[ValueOrHandler[ActionContext, str]]


class EnumDynamicField(BaseDynamicField[Context, str], Generic[Context]):
    TYPE = ActionFieldType.ENUM

    def __init__(
        self,
        enum_values: ValueOrHandler[Context, List[str]],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[Context, bool]] = False,
        is_read_only: Optional[ValueOrHandler[Context, bool]] = False,
        if_: Optional[Awaitable[Any]] = None,
        value: Optional[ValueOrHandler[Context, str]] = None,
        default_value: Optional[ValueOrHandler[Context, str]] = None,
    ):
        super().__init__(label, description, is_required, is_read_only, if_, value, default_value)
        self._enum_values = enum_values

    @property
    def dynamic_fields(self):
        return [*super().dynamic_fields, self._enum_values]

    async def enum_values(self, context: Context) -> List[str]:
        return await self._evaluate(context, self._enum_values)

    async def to_action_field(self, context: Context, default_value: str) -> ActionField:
        res = await super().to_action_field(context, default_value)
        res["enum_values"] = await self.enum_values(context)
        return res

    # @classmethod
    # def from_plain_field(cls, plain_field: PlainEnumDynamicField) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


# enum list
class PlainListEnumDynamicField(PlainField):
    enum_values: ValueOrHandler[ActionContext, List[str]]
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, List[str]]]
    default_value: NotRequired[ValueOrHandler[ActionContext, List[str]]]


class EnumListDynamicField(Generic[Context], BaseDynamicField[Context, List[str]]):
    TYPE = ActionFieldType.ENUM_LIST

    def __init__(
        self,
        enum_values: ValueOrHandler[Context, List[str]],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[Context, bool]] = False,
        is_read_only: Optional[ValueOrHandler[Context, bool]] = False,
        if_: Optional[Awaitable[Any]] = None,
        value: Optional[ValueOrHandler[Context, List[str]]] = None,
        default_value: Optional[ValueOrHandler[Context, List[str]]] = None,
    ):
        super(EnumListDynamicField, self).__init__(
            label, description, is_required, is_read_only, if_, value, default_value
        )
        self._enum_values = enum_values

    @property
    def dynamic_fields(self):
        return [*super(EnumListDynamicField, self).dynamic_fields, self._enum_values]

    async def enum_values(self, context: Context) -> List[str]:
        return await self._evaluate(context, self._enum_values)

    async def to_action_field(self, context: Context, default_value: List[str]) -> ActionField:
        res = await super(EnumListDynamicField, self).to_action_field(context, default_value)
        res["enum_values"] = await self.enum_values(context)
        if res["value"] is None:
            res["value"] = []
        return res

    # unused ???
    # @classmethod
    # def from_plain_field(cls, plain_field: PlainListEnumDynamicField) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


# boolean
class PlainBooleanDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, bool]]
    default_value: NotRequired[ValueOrHandler[ActionContext, bool]]


class BooleanDynamicField(Generic[Context], BaseDynamicField[Context, bool]):
    TYPE = ActionFieldType.BOOLEAN


# number
class PlainNumberDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, Union[int, float]]]
    default_value: NotRequired[ValueOrHandler[ActionContext, Union[int, float]]]


class NumberDynamicField(Generic[Context], BaseDynamicField[Context, Union[int, float]]):
    TYPE = ActionFieldType.NUMBER


# number list
class PlainListNumberDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, Union[int, float]]]
    default_value: NotRequired[ValueOrHandler[ActionContext, Union[int, float]]]


class NumberListDynamicField(Generic[Context], BaseDynamicField[Context, List[Union[int, float]]]):
    TYPE = ActionFieldType.NUMBER_LIST


# string
class PlainStringDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, str]]
    default_value: NotRequired[ValueOrHandler[ActionContext, str]]


class StringDynamicField(Generic[Context], BaseDynamicField[Context, str]):
    TYPE = ActionFieldType.STRING


# string list
class PlainStringListDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, str]]
    default_value: NotRequired[ValueOrHandler[ActionContext, str]]


class StringListDynamicField(Generic[Context], BaseDynamicField[Context, str]):
    TYPE = ActionFieldType.STRING_LIST


# json
class PlainJsonDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, str]]
    default_value: NotRequired[ValueOrHandler[ActionContext, str]]


class JsonDynamicField(Generic[Context], BaseDynamicField[Context, str]):
    TYPE = ActionFieldType.JSON


# file
class FileDynamicField(Generic[Context], BaseDynamicField[Context, File]):
    TYPE = ActionFieldType.FILE


class PlainFileDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, File]]
    default_value: NotRequired[ValueOrHandler[ActionContext, File]]


# file list
class FileListDynamicField(Generic[Context], BaseDynamicField[Context, File]):
    TYPE = ActionFieldType.FILE_LIST


class PlainFileListDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, File]]
    default_value: NotRequired[ValueOrHandler[ActionContext, File]]


DynamicField = Union[
    BooleanDynamicField[Context],
    CollectionDynamicField[Context],
    EnumDynamicField[Context],
    EnumListDynamicField[Context],
    NumberDynamicField[Context],
    StringDynamicField[Context],
    NumberListDynamicField[Context],
    JsonDynamicField[Context],
    FileDynamicField[Context],
]

PlainDynamicField = Union[
    PlainBooleanDynamicField,
    PlainCollectionDynamicField,
    PlainEnumDynamicField,
    PlainListEnumDynamicField,
    PlainNumberDynamicField,
    PlainStringDynamicField,
    PlainListNumberDynamicField,
    PlainJsonDynamicField,
    PlainFileDynamicField,
]


class FieldFactoryException(DatasourceToolkitException):
    pass


class FieldFactory(Generic[Context]):
    FIELD_FOR_TYPE: Any = {
        ActionFieldType.COLLECTION: CollectionDynamicField,
        ActionFieldType.NUMBER: NumberDynamicField,
        ActionFieldType.NUMBER_LIST: NumberListDynamicField,
        ActionFieldType.STRING: StringDynamicField,
        ActionFieldType.STRING_LIST: StringListDynamicField,
        ActionFieldType.BOOLEAN: BooleanDynamicField,
        ActionFieldType.ENUM: EnumDynamicField,
        ActionFieldType.ENUM_LIST: EnumListDynamicField,
        ActionFieldType.JSON: JsonDynamicField,
        ActionFieldType.FILE: FileDynamicField,
        ActionFieldType.FILE_LIST: FileListDynamicField,
    }

    @classmethod
    def build(cls, plain_field: PlainDynamicField) -> DynamicField[Context]:
        try:
            cls_field = cls.FIELD_FOR_TYPE[plain_field["type"]]
        except KeyError:
            raise FieldFactoryException(f"Unknown field type: '{plain_field['type']}'")

        _plain_field = {**plain_field}
        del _plain_field["type"]  # type: ignore
        try:
            return cls_field(**_plain_field)
        except (TypeError, AttributeError) as e:
            raise FieldFactoryException(f"Unable to build a field. cls: '{cls_field.__name__}', e: '{e}'")
