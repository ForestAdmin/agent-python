import json
import uuid
from datetime import date, datetime, time
from typing import Any, List, Optional, Union, cast

from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.fields import PrimitiveType
from forestadmin.datasource_toolkit.validations.types import ValidationPrimaryType, ValidationType, ValidationTypesArray


class TypeGetterException(DatasourceToolkitException):
    pass


class TypeGetter:
    @classmethod
    def get(cls, value: Any, type_context: Optional[PrimitiveType]) -> Union[PrimitiveType, ValidationType]:
        return_mapper = {
            # datetime is also instance of date
            date: lambda: PrimitiveType.DATE_ONLY if not isinstance(value, datetime) else PrimitiveType.DATE,
            datetime: lambda: PrimitiveType.DATE,
            time: lambda: PrimitiveType.TIME_ONLY,
            bytes: lambda: PrimitiveType.BINARY,
            bool: lambda: PrimitiveType.BOOLEAN,
            list: lambda: cls._get_array_type(cast(List[Any], value), type_context),
            str: lambda: cls._get_type_from_string(value, type_context),
            float: lambda: PrimitiveType.NUMBER,
            int: lambda: PrimitiveType.NUMBER,
            dict: lambda: PrimitiveType.JSON if type_context == PrimitiveType.JSON else ValidationPrimaryType.NULL,
            uuid.UUID: lambda: PrimitiveType.UUID,
        }
        for type_, ret_lambda in return_mapper.items():
            if isinstance(value, type_):
                return ret_lambda()

        return ValidationPrimaryType.NULL

    @staticmethod
    def _get_date_type(value: str) -> PrimitiveType:
        if value[-1] == "Z":
            value = value[:-1]  # Python doesn't handle Z in the isoformat
        try:
            date.fromisoformat(value)
        except ValueError:
            pass
        else:
            return PrimitiveType.DATE_ONLY

        try:
            time.fromisoformat(value)
        except ValueError:
            pass
        else:
            PrimitiveType.TIME_ONLY

        try:
            datetime.fromisoformat(value)
        except ValueError:
            pass
        else:
            return PrimitiveType.DATE

        raise TypeGetterException("value is not a primitive date type")

    @staticmethod
    def _is_json_type(value: str) -> bool:
        try:
            res = json.loads(value)
        except (TypeError, json.decoder.JSONDecodeError):
            return False
        else:
            return isinstance(res, dict)

    @staticmethod
    def _is_uuid_type(value: str) -> bool:
        try:
            uuid.UUID(value)
        except ValueError:
            return False
        else:
            return True

    @staticmethod
    def _is_point(value: str, type_context: Optional[PrimitiveType]) -> bool:
        potential_point = value.split(",")
        return (
            len(potential_point) == 2
            and type_context == PrimitiveType.POINT
            and all([TypeGetter.get(p, PrimitiveType.NUMBER) == PrimitiveType.NUMBER for p in potential_point])
        )

    @classmethod
    def _get_type_from_string(cls, value: str, type_context: Optional[PrimitiveType]) -> PrimitiveType:
        try:
            return cls._get_date_type(value)
        except TypeGetterException:
            pass

        if type_context in [PrimitiveType.ENUM, PrimitiveType.STRING, PrimitiveType.BINARY]:
            return type_context
        elif cls._is_json_type(value):
            return PrimitiveType.JSON
        elif cls._is_uuid_type(value):
            return PrimitiveType.UUID
        elif cls._is_point(value, type_context):
            return PrimitiveType.POINT
        return PrimitiveType.STRING

    @classmethod
    def _get_array_type(
        cls, value: List[Any], type_context: Optional[PrimitiveType]
    ) -> Union[PrimitiveType, ValidationType]:
        if len(value) == 0:
            return ValidationTypesArray.EMPTY
        mapping = (
            (PrimitiveType.NUMBER, ValidationTypesArray.NUMBER),
            (PrimitiveType.UUID, ValidationTypesArray.UUID),
            (PrimitiveType.BOOLEAN, ValidationTypesArray.BOOLEAN),
            (PrimitiveType.STRING, ValidationTypesArray.STRING),
            (PrimitiveType.ENUM, ValidationTypesArray.ENUM),
        )
        for type, res in mapping:
            if cls.is_array_of(type, value, type_context):
                return res
        return ValidationPrimaryType.NULL

    @classmethod
    def is_array_of(cls, type: PrimitiveType, values: List[Any], type_context: Optional[PrimitiveType]) -> bool:
        return all([cls.get(value, type_context) == type for value in values])
