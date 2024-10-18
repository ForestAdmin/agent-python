import enum
from typing import Any, Dict, List, Literal, Optional, Set, Union
from uuid import UUID

from typing_extensions import NotRequired, TypedDict, TypeGuard


class Operator(enum.Enum):
    PRESENT = "present"
    BLANK = "blank"
    MISSING = "missing"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    CONTAINS = "contains"
    MATCH = "match"
    # ICONTAINS = "icontains"
    NOT_CONTAINS = "not_contains"
    LONGER_THAN = "longer_than"
    SHORTER_THAN = "shorter_than"
    BEFORE = "before"
    AFTER = "after"
    AFTER_X_HOURS_AGO = "after_x_hours_ago"
    BEFORE_X_HOURS_AGO = "before_x_hours_ago"
    FUTURE = "future"
    PAST = "past"
    PREVIOUS_MONTH_TO_DATE = "previous_month_to_date"
    PREVIOUS_MONTH = "previous_month"
    PREVIOUS_QUARTER_TO_DATE = "previous_quarter_to_date"
    PREVIOUS_QUARTER = "previous_quarter"
    PREVIOUS_WEEK_TO_DATE = "previous_week_to_date"
    PREVIOUS_WEEK = "previous_week"
    PREVIOUS_X_DAYS_TO_DATE = "previous_x_days_to_date"
    PREVIOUS_X_DAYS = "previous_x_days"
    PREVIOUS_YEAR_TO_DATE = "previous_year_to_date"
    PREVIOUS_YEAR = "previous_year"
    TODAY = "today"
    YESTERDAY = "yesterday"
    INCLUDES_ALL = "includes_all"


LITERAL_OPERATORS = Literal[
    "present",
    "blank",
    "missing",
    "equal",
    "not_equal",
    "less_than",
    "greater_than",
    "in",
    "not_in",
    "like",
    "starts_with",
    "ends_with",
    "contains",
    "not_contains",
    "longer_than",
    "shorter_than",
    "before",
    "after",
    "after_x_hours_ago",
    "before_x_hours_ago",
    "future",
    "past",
    "previous_month_to_date",
    "previous_month",
    "previous_quarter_to_date",
    "previous_quarter",
    "previous_week_to_date",
    "previous_week",
    "previous_x_days_to_date",
    "previous_x_days",
    "previous_year_to_date",
    "previous_year",
    "today",
    "yesterday",
    "includes_all",
]


class PrimitiveType(enum.Enum):
    BOOLEAN = "Boolean"
    DATE = "Date"
    DATE_ONLY = "Dateonly"
    ENUM = "Enum"
    JSON = "Json"
    NUMBER = "Number"
    POINT = "Point"
    STRING = "String"
    TIME_ONLY = "Timeonly"
    UUID = "Uuid"
    BINARY = "Binary"


PrimitiveTypeLiteral = Literal[
    "Boolean",
    "Date",
    "Dateonly",
    "Enum",
    "Json",
    "Number",
    "Point",
    "String",
    "Timeonly",
    "Uuid",
    "Binary",
]

LiteralManyToOne = Literal["ManyToOne"]
LiteralOneToOne = Literal["OneToOne"]
LiteralOneToMany = Literal["OneToMany"]
LiteralManyToMany = Literal["ManyToMany"]
LiteralPolymorphicManyToOne = Literal["PolymorphicManyToOne"]
LiteralPolymorphicOneToMany = Literal["PolymorphicOneToMany"]
LiteralPolymorphicOneToOne = Literal["PolymorphicOneToOne"]


class FieldType(enum.Enum):
    COLUMN = "Column"
    MANY_TO_ONE = LiteralManyToOne
    ONE_TO_ONE = LiteralOneToOne
    ONE_TO_MANY = LiteralOneToMany
    MANY_TO_MANY = LiteralManyToMany
    POLYMORPHIC_MANY_TO_ONE = LiteralPolymorphicManyToOne
    POLYMORPHIC_ONE_TO_MANY = LiteralPolymorphicOneToMany
    POLYMORPHIC_ONE_TO_ONE = LiteralPolymorphicOneToOne


class Validation(TypedDict):
    operator: Union[Operator, LITERAL_OPERATORS]
    value: NotRequired[Optional[Any]]


class Column(TypedDict):
    column_type: "ColumnAlias"
    filter_operators: Set[Operator]
    default_value: Optional[Any]
    enum_values: Optional[List[str]]
    is_primary_key: bool
    is_read_only: bool
    is_sortable: bool
    validations: List[Validation]
    type: Literal[FieldType.COLUMN]


class ManyToOne(TypedDict):
    foreign_collection: str
    foreign_key: str
    foreign_key_target: str
    type: Literal[FieldType.MANY_TO_ONE]


class PolymorphicManyToOne(TypedDict):
    foreign_collections: List[str]
    foreign_key: str
    foreign_key_type_field: str
    foreign_key_targets: Dict[str, str]
    type: Literal[FieldType.POLYMORPHIC_MANY_TO_ONE]


class PolymorphicOneToMany(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: str
    type: Literal[FieldType.POLYMORPHIC_ONE_TO_MANY]
    origin_type_field: str
    origin_type_value: str


class PolymorphicOneToOne(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: str
    type: Literal[FieldType.POLYMORPHIC_ONE_TO_ONE]
    origin_type_field: str
    origin_type_value: str


class OneToOne(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: str
    type: Literal[FieldType.ONE_TO_ONE]


class OneToMany(TypedDict):
    foreign_collection: str
    origin_key: str
    origin_key_target: str
    type: Literal[FieldType.ONE_TO_MANY]


class ManyToMany(TypedDict):
    through_collection: str
    foreign_collection: str
    foreign_key: str
    foreign_key_target: str
    foreign_relation: Optional[str]
    origin_key: str
    origin_key_target: str
    type: Literal[FieldType.MANY_TO_MANY]


ColumnAlias = Union[PrimitiveType, PrimitiveTypeLiteral, Dict[str, "ColumnAlias"], List["ColumnAlias"]]
StraightRelationAlias = Union[ManyToMany, ManyToOne, OneToOne, OneToMany]
RelationAlias = Union[
    ManyToMany, ManyToOne, OneToOne, OneToMany, PolymorphicManyToOne, PolymorphicOneToOne, PolymorphicOneToMany
]
PolyRelationAlias = Union[PolymorphicManyToOne, PolymorphicOneToOne, PolymorphicOneToMany]
FieldAlias = Union[Column, RelationAlias]


def is_column(field: "FieldAlias") -> TypeGuard[Column]:
    return field["type"] == FieldType.COLUMN


def is_many_to_one(field: "FieldAlias") -> TypeGuard[ManyToOne]:
    return field["type"] == FieldType.MANY_TO_ONE


def is_polymorphic_many_to_one(field: "FieldAlias") -> TypeGuard[PolymorphicManyToOne]:
    return field["type"] == FieldType.POLYMORPHIC_MANY_TO_ONE


def is_polymorphic_one_to_one(field: "FieldAlias") -> TypeGuard[PolymorphicOneToOne]:
    return field["type"] == FieldType.POLYMORPHIC_ONE_TO_ONE


def is_polymorphic_one_to_many(field: "FieldAlias") -> TypeGuard[PolymorphicOneToMany]:
    return field["type"] == FieldType.POLYMORPHIC_ONE_TO_MANY


def is_one_to_many(field: "FieldAlias") -> TypeGuard[OneToMany]:
    return field["type"] == FieldType.ONE_TO_MANY


def is_one_to_one(field: "FieldAlias") -> TypeGuard[OneToOne]:
    return field["type"] == FieldType.ONE_TO_ONE


def is_many_to_many(field: "FieldAlias") -> TypeGuard[ManyToMany]:
    return field["type"] == FieldType.MANY_TO_MANY


# not used
# def is_polymorphic_relation(field: "FieldAlias") -> TypeGuard[PolyRelationAlias]:
#     return is_polymorphic_many_to_one(field) or is_polymorphic_one_to_many(field) or is_polymorphic_one_to_one(field)


def is_reverse_polymorphic_relation(field: "FieldAlias") -> TypeGuard[Union[PolymorphicOneToMany, PolymorphicOneToOne]]:
    return is_polymorphic_one_to_many(field) or is_polymorphic_one_to_one(field)


def is_straight_relation(field: "FieldAlias") -> TypeGuard[StraightRelationAlias]:
    return is_many_to_one(field) or is_one_to_many(field) or is_one_to_one(field) or is_many_to_many(field)


def is_relation(field: "FieldAlias") -> TypeGuard[RelationAlias]:
    return (
        is_many_to_one(field)
        or is_one_to_many(field)
        or is_one_to_one(field)
        or is_many_to_many(field)
        or is_polymorphic_many_to_one(field)
        or is_polymorphic_one_to_many(field)
        or is_polymorphic_one_to_one(field)
    )


def is_valid_uuid(uuid: str) -> bool:
    try:
        UUID(uuid)
        return True
    except ValueError:
        return False
