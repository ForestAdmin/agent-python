import re
from typing import Any, List, Optional, Pattern, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import LITERAL_OPERATORS, Operator
from forestadmin.datasource_toolkit.interfaces.models.collections import Collection
from forestadmin.datasource_toolkit.interfaces.query.condition_tree.nodes.base import (
    AsyncReplacerAlias,
    CallbackAlias,
    ConditionTree,
    ConditionTreeComponent,
    ReplacerAlias,
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
    return hasattr(tree, "keys") and sorted(tree.keys()) == ["field", "operator"]


class OverrideLeafComponents(ConditionTreeComponent, total=False):
    field: str
    operator: Operator
    value: NotRequired[Optional[Any]]


class ConditionTreeLeaf(ConditionTree):
    def __init__(
        self, field: str, operator: Operator, value: Optional[Any] = None
    ) -> None:
        super().__init__()
        self.field = field
        self.operator = operator
        self.value = value

    def __eq__(self: Self, obj: Self) -> bool:
        return (
            self.__class__ == obj.__class__
            and self.field == obj.field
            and self.operator == obj.operator
            and self.value == obj.value
        )

    def __repr__(self):
        return f"{self.field} {self.operator.value} {self.value}"

    @classmethod
    def load(cls, json: LeafComponents) -> "ConditionTreeLeaf":
        return cls(json["field"], Operator(json["operator"]), json.get("value"))

    @property
    def projection(self) -> Projection:
        return Projection([self.field])

    def inverse(self) -> ConditionTree:
        operator_value: str = self.operator.value

        if f"not_{operator_value}" in Operator.__members__:
            return self.override(
                {
                    "operator": Operator[f"not_{self.operator}"],
                }
            )

        if operator_value.startswith("not_"):
            return self.override({"operator": Operator[self.operator.value[4:]]})

        if self.operator == Operator.BLANK:
            return self.override({"operator": Operator.PRESENT})
        elif self.operator == Operator.PRESENT:
            return self.override({"operator": Operator.BLANK})
        else:
            raise ConditionTreeLeafException(
                f"Operator '{self.operator}' cannot be inverted."
            )

    def __handle_replace_tree(
        self, tree: Union[ConditionTree, ConditionTreeComponent]
    ) -> "ConditionTree":
        if is_leaf_component(tree):
            return ConditionTreeLeaf.load(tree)
        else:
            return cast(ConditionTreeLeaf, tree)

    def replace(self, handler: ReplacerAlias) -> "ConditionTree":
        tree: Union[ConditionTree, ConditionTreeComponent] = handler(self)
        return self.__handle_replace_tree(tree)

    async def replace_async(self, handler: AsyncReplacerAlias) -> "ConditionTree":
        tree: Union[ConditionTree, ConditionTreeComponent] = await handler(self)
        return self.__handle_replace_tree(tree)

    def apply(self, handler: CallbackAlias) -> None:
        return handler(self)

    @property
    def __to_leaf_components(self) -> "LeafComponents":
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
        }

    def override(self, params: "OverrideLeafComponents") -> "ConditionTreeLeaf":
        leaf = cast(LeafComponents, {**self.__to_leaf_components, **params})
        return ConditionTreeLeaf.load(leaf)

    def replace_field(self, field: str) -> "ConditionTreeLeaf":
        return self.override({"field": field})

    def match(
        self, record: RecordsDataAlias, collection: Collection, timezone: str
    ) -> bool:
        field_value = RecordUtils.get_field_value(record, self.field)
        return {
            Operator.EQUAL: field_value == self.value,
            Operator.LESS_THAN: field_value < self.value,
            Operator.GREATER_THAN: field_value > self.value,
            Operator.LIKE: self.__like(field_value),
            Operator.LONGER_THAN: len(cast(str, field_value)) > int(self.value),
            Operator.SHORTER_THAN: len(cast(str, field_value)) < int(self.value),
            Operator.INCLUDES_ALL: self.__includes_all(field_value),
            Operator.NOT_CONTAINS: not self.inverse().match(
                record, collection, timezone
            ),
            Operator.NOT_EQUAL: not self.inverse().match(record, collection, timezone),
        }[self.operator]

    def unnest(self) -> "ConditionTreeLeaf":
        _, name = self.field.split(":")
        return self.override(
            {
                "field": name,
            }
        )

    def nest(self, prefix: str) -> "ConditionTree":
        name = self.field
        if prefix:
            name = f"{prefix}:{name}"
        return self.override(
            {
                "field": name,
            }
        )

    def __includes_all(self, value: Any) -> bool:
        self_values = cast(List[Any], self.value)
        field_values = cast(List[Any], value)
        return all([value in self_values for value in field_values])

    def __like(self, value: str) -> bool:
        if not value:
            return False

        escaped_pattern: str = re.sub(
            r"([\.\\\+\*\?\[\^\]\$\(\)\{\}\=\!\<\>\|\:\-])", "\\\1", self.value
        )
        escaped_pattern = escaped_pattern.replace("%", ".*").replace("_", ".")
        return (
            re.match(
                cast(Pattern[str], f"^{escaped_pattern}$"),
                value,
                cast(re.RegexFlag, "gi"),
            )
            is not None
        )
