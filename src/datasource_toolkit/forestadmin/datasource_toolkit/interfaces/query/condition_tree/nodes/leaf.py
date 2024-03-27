import re
import sys
from typing import Any, Callable, List, Optional, Union, cast

if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import LITERAL_OPERATORS, Operator, is_column
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    AsyncReplacerAlias,
    CallbackAlias,
    ConditionTree,
    ConditionTreeComponent,
    ReplacerAlias,
)
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.operators import (
    INTERVAL_OPERATORS,
    UNIQUE_OPERATORS,
)
from forestadmin.datasource_toolkit.interfaces.query.projections import Projection
from forestadmin.datasource_toolkit.interfaces.records import RecordsDataAlias
from forestadmin.datasource_toolkit.utils.records import RecordUtils
from typing_extensions import NotRequired, Self, TypeGuard


class ConditionTreeLeafException(DatasourceToolkitException):
    pass


class LeafComponents(ConditionTreeComponent):
    field: str
    operator: LITERAL_OPERATORS
    value: NotRequired[Optional[Any]]


def is_leaf_component(tree: Any) -> TypeGuard[LeafComponents]:
    return isinstance(tree, dict) and "field" in tree.keys() and "operator" in tree.keys()


class OverrideLeafComponents(ConditionTreeComponent, total=False):
    field: str
    operator: Operator
    value: NotRequired[Optional[Any]]


class ConditionTreeLeaf(ConditionTree):
    def __init__(self, field: str, operator: Union[Operator, LITERAL_OPERATORS], value: Optional[Any] = None) -> None:
        super().__init__()
        self.field = field
        self.operator = Operator(operator)
        self.value = value

    def __eq__(self: Self, obj: Self) -> bool:  # type: ignore
        return (
            self.__class__ == obj.__class__
            and self.field == obj.field
            and Operator(self.operator) == Operator(obj.operator)
            and self.value == obj.value
        )

    def __repr__(self):
        return f"{self.field} {self.operator.value} {self.value}"

    @property
    def use_interval_operator(self):
        return self.operator in INTERVAL_OPERATORS

    @classmethod
    def load(cls, json: LeafComponents) -> "ConditionTreeLeaf":
        value = json.get("value")
        return cls(json["field"], Operator(json["operator"]), value)

    @property
    def projection(self) -> Projection:
        return Projection(self.field)

    def inverse(self) -> ConditionTree:
        operator_value: str = self.operator.value

        if f"not_{operator_value}" in [o.value for o in Operator]:
            return self.override(
                {
                    "operator": Operator(f"not_{operator_value}"),
                }
            )

        if operator_value.startswith("not_"):
            return self.override({"operator": Operator(self.operator.value[4:])})

        if self.operator == Operator.BLANK:
            return self.override({"operator": Operator.PRESENT})
        elif self.operator == Operator.PRESENT:
            return self.override({"operator": Operator.BLANK})
        else:
            raise ConditionTreeLeafException(f"Operator '{self.operator}' cannot be inverted.")

    @classmethod
    def _handle_replace_tree(cls, tree: Union[ConditionTree, ConditionTreeComponent]) -> "ConditionTree":
        if is_leaf_component(tree):
            return ConditionTreeLeaf.load(tree)  # type: ignore
        else:
            return cast(ConditionTreeLeaf, tree)

    def replace(self, handler: ReplacerAlias) -> "ConditionTree":
        tree: Union[ConditionTree, ConditionTreeComponent] = handler(self)
        return ConditionTreeLeaf._handle_replace_tree(tree)

    async def replace_async(self, handler: AsyncReplacerAlias) -> "ConditionTree":
        tree: Union[ConditionTree, ConditionTreeComponent] = await handler(self)
        return ConditionTreeLeaf._handle_replace_tree(tree)

    def apply(self, handler: CallbackAlias) -> None:
        return handler(self)

    @property
    def _to_leaf_components(self) -> LeafComponents:
        return {
            "field": self.field,
            "operator": self.operator.value,  # type: ignore
            "value": self.value,
        }

    def override(self, params: "OverrideLeafComponents") -> "ConditionTreeLeaf":
        leaf = cast(LeafComponents, {**self._to_leaf_components, **params})
        return ConditionTreeLeaf.load(leaf)

    def replace_field(self, field: str) -> "ConditionTreeLeaf":
        return self.override({"field": field})

    def _verify_is_number_values(self, value: Union[float, int]):
        if not all([(isinstance(v, int) or isinstance(v, float)) for v in [value, self.value]]):
            raise ConditionTreeLeafException(f"Should be numbers ({value}, {self.value})")

    def _equal(self, value: Any) -> bool:
        return self.value == value

    def _less_than(self, value: Union[int, float]) -> bool:
        self._verify_is_number_values(value)
        return value < self.value  # type: ignore

    def _greater_than(self, value: Union[int, float]) -> bool:
        self._verify_is_number_values(value)
        return value > self.value  # type: ignore

    def _longer_than(self, value: str) -> bool:
        try:
            return len(value) > self.value  # type: ignore
        except TypeError:
            raise ConditionTreeLeafException(
                f"Should have a string and an integer as argument \
                 to compare length to something ({value} {self.value}"
            )

    def _shorter_than(self, value: str) -> bool:
        try:
            return len(value) < self.value  # type: ignore
        except TypeError:
            raise ConditionTreeLeafException(
                f"Should have a string and an integer as argument \
                 to compare length to something ({value} {self.value}"
            )

    def _not_equal_not_contains(
        self, record: RecordsDataAlias, collection: Collection, timezone: zoneinfo.ZoneInfo
    ) -> Callable[[Any], bool]:
        def wrapper(value: Any) -> bool:
            return not self.inverse().match(record, collection, timezone)

        return wrapper

    def match(self, record: RecordsDataAlias, collection: Collection, timezone: zoneinfo.ZoneInfo) -> bool:
        from forestadmin.datasource_toolkit.utils.collections import CollectionUtils

        field_value = RecordUtils.get_field_value(record, self.field)
        not_equal_not_contains = self._not_equal_not_contains(record, collection, timezone)
        try:
            return {
                Operator.EQUAL: self._equal,
                Operator.LESS_THAN: self._less_than,
                Operator.GREATER_THAN: self._greater_than,
                Operator.LIKE: self._like,
                Operator.LONGER_THAN: self._longer_than,
                Operator.SHORTER_THAN: self._shorter_than,
                Operator.INCLUDES_ALL: self._includes_all,
                Operator.NOT_CONTAINS: not_equal_not_contains,
                Operator.NOT_EQUAL: not_equal_not_contains,
            }[self.operator](field_value)
        except KeyError:
            from forestadmin.datasource_toolkit.interfaces.query.condition_tree.equivalence import (
                ConditionTreeEquivalent,
            )

            column_type = CollectionUtils.get_field_schema(collection, self.field)
            if is_column(column_type):
                equivalent_tree = ConditionTreeEquivalent.get_equivalent_tree(
                    self,
                    UNIQUE_OPERATORS,
                    column_type["column_type"],
                    timezone,
                )
                if equivalent_tree:
                    return equivalent_tree.match(record, collection, timezone)
            else:
                raise ConditionTreeLeafException(
                    f"You can't find an equivalent for this kind of field ({column_type['type']})"
                )
        return False

    def some_leaf(self, handler: Callable[["ConditionTreeLeaf"], bool]) -> bool:  # noqa:F821
        return handler(self)

    def unnest(self) -> "ConditionTreeLeaf":
        splited = self.field.split(":")
        if len(splited) > 1:
            return self.override(
                {
                    "field": ":".join(splited[1:]),
                }
            )
        raise ConditionTreeLeafException(f"Unable to unset {self.field}")

    def nest(self, prefix: str) -> "ConditionTree":
        name = self.field
        if prefix:
            name = f"{prefix}:{name}"
        else:
            raise ConditionTreeLeafException("Unable to nest with an empty prefix")
        return self.override(
            {
                "field": name,
            }
        )

    def _includes_all(self, value: Any) -> bool:
        self_values = cast(List[Any], self.value)
        field_values = cast(List[Any], value)
        return all([value in self_values for value in field_values])

    def _like(self, value: str) -> bool:
        if not value:
            return False

        escaped_pattern: str = re.sub(
            r"([\.\\\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:\-])",  # type: ignore
            "\\\1",  # type: ignore
            self.value,  # type: ignore
        )
        escaped_pattern = escaped_pattern.replace("%", ".*").replace("_", ".")
        return (
            re.match(
                f"^{escaped_pattern}$",
                value,
                re.I,
            )
            is not None
        )

    def to_plain_object(self) -> LeafComponents:  # type: ignore
        return LeafComponents(
            field=self.field,
            operator=self.operator.value,  # type: ignore
            value=self.value,
        )
