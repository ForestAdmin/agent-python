from datetime import date, datetime
from typing import Any, Awaitable, Callable, Generic, List, Literal, Optional, TypeVar, Union

from forestadmin.datasource_toolkit.decorators.action.context.base import ActionContext
from forestadmin.datasource_toolkit.decorators.action.types.widgets import (
    WIDGET_ATTRIBUTES,
    AddressAutocompleteFieldConfiguration,
    ArrayTextInputFieldConfiguration,
    CheckboxesFieldConfiguration,
    CheckboxFieldConfiguration,
    ColorPickerFieldConfiguration,
    CurrencyInputFieldConfiguration,
    DatePickerFieldConfiguration,
    DropdownDynamicFieldConfiguration,
    DropdownDynamicSearchFieldConfiguration,
    FileListPickerFieldConfiguration,
    FilePickerFieldConfiguration,
    JsonEditorFieldConfiguration,
    NumberInputFieldConfiguration,
    NumberInputListFieldConfiguration,
    RadioButtonFieldConfiguration,
    RichTextFieldConfiguration,
    TextAreaFieldConfiguration,
    TextInputFieldConfiguration,
    TimePickerFieldConfiguration,
    UserDropdownFieldConfiguration,
)
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionField,
    ActionFieldType,
    ActionFieldTypeLiteral,
    File,
    WidgetTypes,
)
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias
from typing_extensions import NotRequired, TypedDict

Number = Union[int, float]
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
    WIDGET_ATTR_TO_EVALUATE = ("min", "max", "step", "base", "extensions", "max_size_mb", "max_count", "options")
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
        **kwargs,
    ):
        self.label = label
        self.description = description
        self._is_required = is_required
        self._is_read_only = is_read_only
        self._if_ = if_
        self._value = value
        self._default_value = default_value

        unknown_keyword_args = [k for k in kwargs.keys() if k not in WIDGET_ATTRIBUTES]
        if any(unknown_keyword_args):
            raise TypeError(
                f"BaseDynamicField.__init__() got an unexpected keyword argument '{unknown_keyword_args[0]}'"
            )
        self._widget_fields = kwargs

    @property
    def dynamic_fields(self):
        ret = [getattr(self, f"_{field}") for field in BaseDynamicField.ATTR_TO_EVALUATE]
        if len(self._widget_fields) > 0:
            ret.extend(self._widget_fields.get(widget_attr) for widget_attr in BaseDynamicField.WIDGET_ATTR_TO_EVALUATE)
        return ret

    @property
    def is_dynamic(self):
        return any(map(lambda x: isinstance(x, Callable), self.dynamic_fields))

    async def to_action_field(
        self, context: Context, default_value: Result, search_value: Optional[str] = None
    ) -> ActionField:
        field = ActionField(
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
            **{k: await self._evaluate(context, v) for k, v in self._widget_fields.items() if k != "options"},
        )
        if "options" in self._widget_fields:
            field["options"] = await self._evaluate_option(context, self._widget_fields["options"], search_value)
        return field

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

    async def _evaluate_option(
        self, context: Context, attribute: ValueOrHandler[ActionContext, Any], search_value: Optional[str]
    ):
        if self._widget_fields.get("search", "") == "dynamic":
            res = self._widget_fields["options"](context, search_value)
            if isinstance(res, Awaitable):
                return await res
            return res
        return await self._evaluate(context, attribute)


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

    async def to_action_field(
        self, context: Context, default_value: str, search_value: Optional[str] = None
    ) -> ActionField:
        res = await super().to_action_field(context, default_value, search_value)
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


# boolean
class PlainBooleanDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, bool]]
    default_value: NotRequired[ValueOrHandler[ActionContext, bool]]


class BooleanDynamicField(Generic[Context], BaseDynamicField[Context, bool]):
    TYPE = ActionFieldType.BOOLEAN


# date only
class PlainDateOnlyDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, date]]
    default_value: NotRequired[ValueOrHandler[ActionContext, date]]


class DateOnlyDynamicField(Generic[Context], BaseDynamicField[Context, date]):
    TYPE = ActionFieldType.DATE_ONLY


# datetime
class PlainDateTimeDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, datetime]]
    default_value: NotRequired[ValueOrHandler[ActionContext, datetime]]


class DateTimeDynamicField(Generic[Context], BaseDynamicField[Context, datetime]):
    TYPE = ActionFieldType.DATE


# time
class PlainTimeDynamicField(PlainField):
    if_: NotRequired[ValueOrHandler[ActionContext, Any]]
    value: NotRequired[ValueOrHandler[ActionContext, str]]
    default_value: NotRequired[ValueOrHandler[ActionContext, str]]


class TimeDynamicField(Generic[Context], BaseDynamicField[Context, str]):
    TYPE = ActionFieldType.TIME


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


# declare widget for field types
class PlainStringDynamicFieldColorWidget(PlainStringDynamicField, ColorPickerFieldConfiguration):
    pass


class PlainStringDynamicFieldTextInputWidget(PlainStringDynamicField, TextInputFieldConfiguration):
    pass


class PlainStringDynamicFieldTextAreaWidget(PlainStringDynamicField, TextAreaFieldConfiguration):
    pass


class PlainStringDynamicFieldRichTextWidget(PlainStringDynamicField, RichTextFieldConfiguration):
    pass


class PlainStringDynamicFieldAddressAutocompleteWidget(PlainStringDynamicField, AddressAutocompleteFieldConfiguration):
    pass


class PlainStringListDynamicFieldTextInputListWidget(PlainStringListDynamicField, ArrayTextInputFieldConfiguration):
    pass


class PlainNumberDynamicFieldNumberInputWidget(PlainNumberDynamicField, NumberInputFieldConfiguration):
    pass


class PlainNumberDynamicFieldCurrencyInputWidget(PlainNumberDynamicField, CurrencyInputFieldConfiguration):
    pass


class PlainListNumberDynamicFieldNumberInputListWidget(PlainListNumberDynamicField, NumberInputListFieldConfiguration):
    pass


class PlainJsonDynamicFieldJsonEditorWidget(PlainJsonDynamicField, JsonEditorFieldConfiguration):
    pass


class PlainFileDynamicFieldFilePickerWidget(PlainFileDynamicField, FilePickerFieldConfiguration):
    pass


class PlainFileListDynamicFieldFilePickerWidget(PlainFileListDynamicField, FileListPickerFieldConfiguration):
    pass


class PlainDateDynamicFieldDatePickerWidget(PlainDateTimeDynamicField, DatePickerFieldConfiguration):
    pass


class PlainDateOnlyDynamicFieldDatePickerWidget(PlainDateOnlyDynamicField, DatePickerFieldConfiguration):
    pass


class PlainTimeDynamicFieldTimePickerWidget(PlainTimeDynamicField, TimePickerFieldConfiguration):
    pass


class PlainBooleanDynamicFieldCheckboxWidget(PlainBooleanDynamicField, CheckboxFieldConfiguration):
    pass


class PlainStringDynamicFieldRadioButtonWidget(PlainStringDynamicField, RadioButtonFieldConfiguration[str]):
    pass


class PlainNumberDynamicFieldRadioButtonWidget(PlainNumberDynamicField, RadioButtonFieldConfiguration[Number]):
    pass


class PlainStringListDynamicFieldRadioButtonWidget(PlainStringListDynamicField, CheckboxesFieldConfiguration[str]):
    pass


class PlainListNumberDynamicFieldRadioButtonWidget(PlainListNumberDynamicField, CheckboxesFieldConfiguration[Number]):
    pass


class PlainNumberDynamicFieldDropdownWidget(PlainNumberDynamicField, DropdownDynamicFieldConfiguration[Number]):
    pass


class PlainListNumberDynamicFieldDropdownWidget(PlainListNumberDynamicField, DropdownDynamicFieldConfiguration[Number]):
    pass


class PlainStringDynamicFieldDropdownWidget(PlainStringDynamicField, DropdownDynamicFieldConfiguration[str]):
    pass


class PlainStringListDynamicFieldDropdownWidget(PlainStringListDynamicField, DropdownDynamicFieldConfiguration[str]):
    pass


class PlainNumberDynamicFieldDropdownSearchWidget(
    PlainNumberDynamicField, DropdownDynamicSearchFieldConfiguration[Number]
):
    pass


class PlainListNumberDynamicFieldDropdownSearchWidget(
    PlainListNumberDynamicField, DropdownDynamicSearchFieldConfiguration[Number]
):
    pass


class PlainStringDynamicFieldDropdownSearchWidget(
    PlainStringDynamicField, DropdownDynamicSearchFieldConfiguration[str]
):
    pass


class PlainStringListDynamicFieldDropdownSearchWidget(
    PlainStringListDynamicField, DropdownDynamicSearchFieldConfiguration[str]
):
    pass


# user dropdown
class PlainStringListDynamicFieldUserDropdownFieldConfiguration(
    PlainStringListDynamicField, UserDropdownFieldConfiguration
):
    pass


class PlainStringDynamicFieldUserDropdownFieldConfiguration(PlainStringDynamicField, UserDropdownFieldConfiguration):
    pass


class WidgetTyping(TypedDict):
    type: Union[ActionFieldType, ActionFieldTypeLiteral]
    widget: WidgetTypes
    search: Literal["static", "dynamic", "disabled"]


PlainDynamicField = Union[
    # boolean
    PlainBooleanDynamicField,
    PlainBooleanDynamicFieldCheckboxWidget,
    # collection
    PlainCollectionDynamicField,
    # enum
    PlainEnumDynamicField,
    PlainListEnumDynamicField,
    # number & widgets
    PlainNumberDynamicField,
    PlainNumberDynamicFieldNumberInputWidget,
    PlainNumberDynamicFieldCurrencyInputWidget,
    PlainNumberDynamicFieldRadioButtonWidget,
    PlainNumberDynamicFieldDropdownWidget,
    PlainNumberDynamicFieldDropdownSearchWidget,
    # number list & widgets
    PlainListNumberDynamicField,
    PlainListNumberDynamicFieldNumberInputListWidget,
    PlainListNumberDynamicFieldRadioButtonWidget,
    PlainListNumberDynamicFieldDropdownWidget,
    PlainListNumberDynamicFieldDropdownSearchWidget,
    # string & widgets
    PlainStringDynamicField,
    PlainStringDynamicFieldColorWidget,
    PlainStringDynamicFieldTextInputWidget,
    PlainStringDynamicFieldTextAreaWidget,
    PlainStringDynamicFieldRichTextWidget,
    PlainStringDynamicFieldAddressAutocompleteWidget,
    PlainStringDynamicFieldRadioButtonWidget,
    PlainStringDynamicFieldDropdownWidget,
    PlainStringDynamicFieldDropdownSearchWidget,
    PlainStringDynamicFieldUserDropdownFieldConfiguration,
    # string list & widgets
    PlainStringListDynamicField,
    PlainStringListDynamicFieldTextInputListWidget,
    PlainStringListDynamicFieldRadioButtonWidget,
    PlainStringListDynamicFieldDropdownWidget,
    PlainStringListDynamicFieldDropdownSearchWidget,
    PlainStringListDynamicFieldUserDropdownFieldConfiguration,
    # json
    PlainJsonDynamicField,
    PlainJsonDynamicFieldJsonEditorWidget,
    # file
    PlainFileDynamicField,
    PlainFileDynamicFieldFilePickerWidget,
    # file list
    PlainFileListDynamicField,
    PlainFileListDynamicFieldFilePickerWidget,
    # date
    PlainDateTimeDynamicField,
    PlainDateDynamicFieldDatePickerWidget,
    # date only
    PlainDateOnlyDynamicField,
    PlainDateDynamicFieldDatePickerWidget,
    # time
    PlainTimeDynamicField,
    PlainTimeDynamicFieldTimePickerWidget,
    # for autocompletion
    WidgetTyping,  # this one must be the latest by name class (alphabetic order)
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
        ActionFieldType.TIME: TimeDynamicField,
        ActionFieldType.DATE: DateTimeDynamicField,
        ActionFieldType.DATE_ONLY: DateOnlyDynamicField,
    }

    @classmethod
    def build(cls, plain_field: PlainDynamicField) -> DynamicField[Context]:
        try:
            cls_field = cls.FIELD_FOR_TYPE[ActionFieldType(plain_field["type"])]
        except (KeyError, ValueError):
            raise FieldFactoryException(f"Unknown field type: '{plain_field['type']}'")

        _plain_field = {**plain_field}
        del _plain_field["type"]  # type: ignore
        try:
            return cls_field(**_plain_field)
        except (TypeError, AttributeError) as e:
            raise FieldFactoryException(f"Unable to build a field. cls: '{cls_field.__name__}', e: '{e}'")
