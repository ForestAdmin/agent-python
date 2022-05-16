import enum
from typing import Union


class ValidationTypesArray(enum.Enum):
    BOOLEAN = "ArrayOfBoolean"
    ENUM = "ArrayOfEnum"
    NUMBER = "ArrayOfNumber"
    STRING = "ArrayOfString"
    UUID = "ArrayOfUuid"
    EMPTY = "EmptyArray"


class ValidationPrimaryType(enum.Enum):
    NULL = "Null"


ValidationType = Union[ValidationTypesArray, ValidationPrimaryType]
