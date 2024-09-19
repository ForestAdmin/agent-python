import abc
from datetime import date, datetime
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.context.bulk import ActionContextBulk
from forestadmin.datasource_toolkit.decorators.action.context.single import ActionContextSingle
from forestadmin.datasource_toolkit.decorators.action.types.fields import PlainDynamicField
from forestadmin.datasource_toolkit.decorators.action.types.widgets import COMPONENT_ATTRIBUTES, WIDGET_ATTRIBUTES
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionField,
    ActionFieldType,
    ActionFormElement,
    ActionLayoutElement,
    File,
    LayoutComponentTypes,
)
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from forestadmin.datasource_toolkit.utils.user_callable import call_user_function

Number = Union[int, float]
Context = Union[ActionContext, ActionContextSingle, ActionContextBulk]
Result = TypeVar("Result")

ValueOrHandler = Union[
    Callable[[ActionContext], Union[Awaitable[Result], Result]],
    Callable[[ActionContextSingle], Union[Awaitable[Result], Result]],
    Callable[[ActionContextBulk], Union[Awaitable[Result], Result]],
    Result,
]


class BaseDynamicFormElement:
    ATTR_TO_EVALUATE = ("if_",)
    EXTRA_ATTR_TO_EVALUATE = ()
    TYPE: ActionFieldType

    def __init__(
        self,
        if_: Optional[ValueOrHandler[bool]] = None,
        **extra_attr_fields: Dict[str, Any],
    ):
        self._if_ = if_
        self.extra_attr_fields = extra_attr_fields

    @abc.abstractmethod
    async def to_action_field(
        self, context: Context, default_value: Any, search_value: Optional[str] = None
    ) -> ActionFormElement:
        pass

    @property
    def dynamic_fields(self) -> List[Any]:
        ret = [getattr(self, f"_{field}") for field in self.ATTR_TO_EVALUATE]

        if len(self.extra_attr_fields) > 0:
            ret.extend(self.extra_attr_fields.get(widget_attr) for widget_attr in self.EXTRA_ATTR_TO_EVALUATE)
        return ret

    @property
    def is_dynamic(self) -> bool:
        """return True if this field is dynamic"""
        return any(map(lambda x: callable(x), self.dynamic_fields))

    async def if_(self, context: Context) -> Any:
        return self._if_ is None or await self._evaluate(context, self._if_)

    async def _evaluate(self, context: Context, attribute: ValueOrHandler[Any]) -> Any:
        if callable(attribute):
            return await call_user_function(attribute, context)
        else:
            return attribute


class DynamicLayoutElements(BaseDynamicFormElement):
    TYPE = ActionFieldType.LAYOUT

    def __init__(
        self,
        component: LayoutComponentTypes,
        if_: Optional[ValueOrHandler[bool]] = None,
        **component_fields: Dict[str, Any],
    ):
        self._component: LayoutComponentTypes = component

        unknown_keyword_args = [k for k in component_fields.keys() if k not in COMPONENT_ATTRIBUTES]
        if any(unknown_keyword_args):
            raise TypeError(
                f"{self.__class__.__name__}.__init__() got an unexpected keyword argument '{unknown_keyword_args[0]}'"
            )
        super().__init__(if_, **component_fields)

    @property
    def is_dynamic(self) -> bool:
        # TODO: restore the real computation for story#7
        return True

    async def to_action_field(
        self, context: Context, default_value: Any, search_value: Optional[str] = None
    ) -> ActionLayoutElement:
        # here default value is the all form_values dict because of possible nested fields
        return ActionLayoutElement(type=self.TYPE, component=self._component)


class BaseDynamicField(BaseDynamicFormElement, Generic[Result]):
    ATTR_TO_EVALUATE = (
        *BaseDynamicFormElement.ATTR_TO_EVALUATE,
        "is_required",
        "is_read_only",
        "value",
        "description",
        "default_value",
    )
    WIDGET_ATTR_TO_EVALUATE = (
        *BaseDynamicFormElement.EXTRA_ATTR_TO_EVALUATE,
        "min",
        "max",
        "step",
        "base",
        "extensions",
        "max_size_mb",
        "max_count",
        "options",
    )

    def __init__(
        self,
        label: str,
        description: Optional[ValueOrHandler[str]] = "",
        is_required: Optional[ValueOrHandler[bool]] = False,
        is_read_only: Optional[ValueOrHandler[bool]] = False,
        if_: Optional[ValueOrHandler[bool]] = None,
        value: Optional[ValueOrHandler[Result]] = None,
        default_value: Optional[ValueOrHandler[Result]] = None,
        **kwargs: Dict[str, Any],
    ):
        self.label = label
        self._description = description
        self._is_required = is_required
        self._is_read_only = is_read_only
        self._value = value
        self._default_value = default_value

        unknown_keyword_args = [k for k in kwargs.keys() if k not in WIDGET_ATTRIBUTES]
        if any(unknown_keyword_args):
            raise TypeError(
                f"{self.__class__.__name__}.__init__() got an unexpected keyword argument '{unknown_keyword_args[0]}'"
            )
        super().__init__(if_, **kwargs)

    async def to_action_field(
        self, context: Context, default_value: Result, search_value: Optional[str] = None
    ) -> ActionField:
        field = ActionField(
            type=self.TYPE,
            label=self.label,
            description=await self.description(context),
            is_read_only=await self.is_read_only(context),
            is_required=await self.is_required(context),
            value=await self.value(context) or default_value,
            default_value=await self.default_value(context),
            collection_name=None,
            enum_values=None,
            watch_changes=False,
            **{k: await self._evaluate(context, v) for k, v in self.extra_attr_fields.items() if k != "options"},
        )
        if "options" in self.extra_attr_fields:
            field["options"] = await self._evaluate_option(context, self.extra_attr_fields["options"], search_value)
        return field

    async def default_value(self, context: Context) -> Result:
        return await self._evaluate(context, self._default_value)

    async def is_required(self, context: Context) -> bool:
        return await self._evaluate(context, self._is_required)

    async def description(self, context: Context) -> str:
        return await self._evaluate(context, self._description)

    async def is_read_only(self, context: Context) -> bool:
        return await self._evaluate(context, self._is_read_only)

    async def value(self, context: Context) -> Result:
        return await self._evaluate(context, self._value)

    async def _evaluate_option(self, context: Context, attribute: ValueOrHandler[Any], search_value: Optional[str]):
        if self.extra_attr_fields.get("search", "") == "dynamic":
            return await call_user_function(self.extra_attr_fields["options"], context, search_value)
        else:
            return await self._evaluate(context, attribute)


class CollectionDynamicField(BaseDynamicField[CompositeIdAlias]):
    TYPE = ActionFieldType.COLLECTION

    def __init__(
        self,
        collection_name: ValueOrHandler[str],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[bool]] = False,
        is_read_only: Optional[ValueOrHandler[bool]] = False,
        if_: Optional[ValueOrHandler[bool]] = None,
        value: Optional[ValueOrHandler[CompositeIdAlias]] = None,
        default_value: Optional[ValueOrHandler[CompositeIdAlias]] = None,
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

    async def to_action_field(
        self, context: Context, default_value: CompositeIdAlias, search_value: Optional[str] = None
    ) -> ActionField:
        res = await super(CollectionDynamicField, self).to_action_field(context, default_value, search_value)
        res["collection_name"] = await self.collection_name(context)
        return res

    # @classmethod
    # def from_plain_field(  # type: ignore
    #     cls, plain_field: PlainCollectionDynamicField
    # ) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


class EnumDynamicField(BaseDynamicField[str]):
    TYPE = ActionFieldType.ENUM

    def __init__(
        self,
        enum_values: ValueOrHandler[List[str]],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[bool]] = False,
        is_read_only: Optional[ValueOrHandler[bool]] = False,
        if_: Optional[ValueOrHandler[bool]] = None,
        value: Optional[ValueOrHandler[str]] = None,
        default_value: Optional[ValueOrHandler[str]] = None,
    ):
        super().__init__(label, description, is_required, is_read_only, if_, value, default_value)
        self._enum_values = enum_values

    @property
    def dynamic_fields(self):
        return [*super().dynamic_fields, self._enum_values]

    async def enum_values(self, context: Context) -> List[str]:
        return await self._evaluate(context, self._enum_values)

    async def to_action_field(
        self, context: Context, default_value: str, search_value: Optional[str] = None
    ) -> ActionField:
        res = await super().to_action_field(context, default_value, search_value)
        res["enum_values"] = await self.enum_values(context)
        return res

    # @classmethod
    # def from_plain_field(cls, plain_field: PlainEnumDynamicField) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


class EnumListDynamicField(BaseDynamicField[List[str]]):
    TYPE = ActionFieldType.ENUM_LIST

    def __init__(
        self,
        enum_values: ValueOrHandler[List[str]],
        label: str,
        description: Optional[str] = "",
        is_required: Optional[ValueOrHandler[bool]] = False,
        is_read_only: Optional[ValueOrHandler[bool]] = False,
        if_: Optional[ValueOrHandler[bool]] = None,
        value: Optional[ValueOrHandler[List[str]]] = None,
        default_value: Optional[ValueOrHandler[List[str]]] = None,
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

    async def to_action_field(
        self, context: Context, default_value: List[str], search_value: Optional[str] = None
    ) -> ActionField:
        res = await super(EnumListDynamicField, self).to_action_field(context, default_value, search_value)
        res["enum_values"] = await self.enum_values(context)
        if res.get("value") is None:
            res["value"] = []
        return res

    # unused ???
    # @classmethod
    # def from_plain_field(cls, plain_field: PlainListEnumDynamicField) -> Self:  # type: ignore
    #     return cls(**plain_field)  # type: ignore


class BooleanDynamicField(BaseDynamicField[bool]):
    TYPE = ActionFieldType.BOOLEAN


class DateOnlyDynamicField(BaseDynamicField[date]):
    TYPE = ActionFieldType.DATE_ONLY


class DateTimeDynamicField(BaseDynamicField[datetime]):
    TYPE = ActionFieldType.DATE


class TimeDynamicField(BaseDynamicField[str]):
    TYPE = ActionFieldType.TIME


class NumberDynamicField(BaseDynamicField[Number]):
    TYPE = ActionFieldType.NUMBER


class NumberListDynamicField(BaseDynamicField[List[Number]]):
    TYPE = ActionFieldType.NUMBER_LIST


class StringDynamicField(BaseDynamicField[str]):
    TYPE = ActionFieldType.STRING


class StringListDynamicField(BaseDynamicField[str]):
    TYPE = ActionFieldType.STRING_LIST


class JsonDynamicField(BaseDynamicField[str]):
    TYPE = ActionFieldType.JSON


class FileDynamicField(BaseDynamicField[File]):
    TYPE = ActionFieldType.FILE

    @property
    def is_dynamic(self) -> bool:
        return self._default_value is not None or super().is_dynamic


class FileListDynamicField(BaseDynamicField[List[File]]):
    TYPE = ActionFieldType.FILE_LIST

    @property
    def is_dynamic(self) -> bool:
        return self._default_value is not None or super().is_dynamic


DynamicFields = Union[
    BooleanDynamicField,
    CollectionDynamicField,
    EnumDynamicField,
    EnumListDynamicField,
    NumberDynamicField,
    NumberListDynamicField,
    StringDynamicField,
    StringListDynamicField,
    JsonDynamicField,
    FileDynamicField,
    DateTimeDynamicField,
    DateOnlyDynamicField,
    TimeDynamicField,
    FileListDynamicField,
]
DynamicFormElements = Union[DynamicFields, DynamicLayoutElements]


class FormElementFactoryException(DatasourceToolkitException):
    pass


class FormElementFactory:
    FIELD_FOR_TYPE: Dict[ActionFieldType, Type[DynamicFormElements]] = {
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
        ActionFieldType.TIME: TimeDynamicField,
        ActionFieldType.DATE: DateTimeDynamicField,
        ActionFieldType.DATE_ONLY: DateOnlyDynamicField,
        ActionFieldType.LAYOUT: DynamicLayoutElements,
    }

    @classmethod
    def build(cls, plain_field: PlainDynamicField) -> DynamicFormElements:
        try:
            cls_field = cls.FIELD_FOR_TYPE[ActionFieldType(plain_field["type"])]
        except (KeyError, ValueError):
            raise FormElementFactoryException(f"Unknown field type: '{plain_field['type']}'")

        _plain_field: Dict[str, Any] = {**plain_field}
        del _plain_field["type"]
        try:
            return cls_field(**_plain_field)
        except (TypeError, AttributeError) as e:
            raise FormElementFactoryException(f"Unable to build a field. cls: '{cls_field.__name__}', e: '{e}'")
