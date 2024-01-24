from base64 import b64decode, b64encode
from typing import Any, Dict, List, cast
from urllib.parse import quote, unquote

from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerActionField
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType, File
from forestadmin.datasource_toolkit.interfaces.records import CompositeIdAlias


class ForestValueConverterException(DatasourceToolkitException):
    pass


class ForestValueConverter:
    @staticmethod
    def make_form_data_from_fields(
        datasource: Datasource[Collection], fields: List[ForestServerActionField]
    ) -> Dict[str, Any]:
        form_data: Dict[str, Any] = {}
        for field in fields:
            if field["reference"] and field["value"]:
                collection_name = field["reference"].split(":")[0]
                collection = datasource.get_collection(collection_name)
                form_data[field["field"]] = unpack_id(collection.schema, field["value"])
            elif field["type"] == ActionFieldType.FILE.value:
                form_data[field["field"]] = ForestValueConverter._parse_data_uri(field["value"])
            elif (isinstance(field["type"], list) and field["type"][0] == ActionFieldType.FILE.value) or (
                field["type"] == ActionFieldType.FILE_LIST
            ):
                form_data[field["field"]] = [ForestValueConverter._parse_data_uri(value) for value in field["value"]]
            else:
                form_data[field["field"]] = field["value"]
        return form_data

    @staticmethod
    def make_form_unsafe_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        This last form data parser tries to guess the types from the data itself.

        - Fields with type "Collection" which target collections where the pk is not a string or
        derivative (mongoid, uuid, ...) won't be parser correctly, as we don't have enough information
        to properly guess the type
        - Fields of type "String" but where the final user entered a data-uri manually in the frontend
        will be wrongfully parsed.
        """
        data = {}
        for key, value in raw_data.items():
            if isinstance(value, list) and all([ForestValueConverter.is_data_uri(v) for v in value]):
                data[key] = [ForestValueConverter._parse_data_uri(v) for v in value]
            elif ForestValueConverter.is_data_uri(value):
                data[key] = ForestValueConverter._parse_data_uri(value)
            else:
                data[key] = value
        return data

    @staticmethod
    def make_form_data(
        datasource: Datasource[Collection], raw_data: Dict[str, Any], fields: List[ActionField]
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, value in raw_data.items():
            _fields = list(filter(lambda f: f["label"] == key, fields))  # type: ignore
            if len(_fields) != 1:
                continue
            field: ActionField = _fields[0]
            if field["type"] == ActionFieldType.COLLECTION and value:
                collection = datasource.get_collection(cast(str, field["collection_name"]))
                data[key] = unpack_id(collection.schema, value)

            elif field["type"] == ActionFieldType.FILE:
                data[key] = ForestValueConverter._parse_data_uri(value)

            elif field["type"] == ActionFieldType.FILE_LIST:
                data[key] = [ForestValueConverter._parse_data_uri(v) for v in value]
            else:
                data[key] = value
        return data

    @staticmethod
    def value_to_forest(field: ActionField, value: Any) -> Any:
        if field["type"] == ActionFieldType.ENUM:
            if not field["enum_values"] or ((value is not None) and value not in field["enum_values"]):
                raise ForestValueConverterException(f"{value} is not in {field['enum_values']}")
            return value

        elif field["type"] == ActionFieldType.ENUM_LIST and value:
            for v in cast(List[str], value):
                if not field["enum_values"] or v not in field["enum_values"]:
                    raise ForestValueConverterException(f"{v} is not in {field['enum_values']}")
            return value

        elif field["type"] == ActionFieldType.COLLECTION and value:
            value = cast(CompositeIdAlias, value)
            return "|".join(value)

        elif field["type"] == ActionFieldType.FILE and value:
            return ForestValueConverter._make_data_uri(value)
        elif field["type"] == ActionFieldType.FILE_LIST:
            return [ForestValueConverter._make_data_uri(v) for v in value] if isinstance(value, list) else []

        return value

    @staticmethod
    def is_data_uri(value: str) -> bool:
        return isinstance(value, str) and value.startswith("data:")

    @staticmethod
    def _parse_data_uri(file: str) -> File:
        if not file:
            return None

        # Poor man's data uri parser (spec compliants one don't get the filename).
        # Hopefully this does not break.
        (header, data) = file[5:].split(",", 1)
        (mime_type, *media_types) = header.split(";")
        result = {"mime_type": mime_type, "buffer": b64decode(data)}
        for media_type in media_types:
            index = media_type.find("=")
            if index != -1:
                result[media_type[0:index]] = unquote(media_type[index + 1 :])
        return File(**result)

    @staticmethod
    def _make_data_uri(file: File) -> str:
        if not file:
            return None

        buffer = b64encode(file.buffer).decode("utf-8")

        media_types = {"name": file.name, "charset": file.charset}
        media_types = ";".join([f"{key}={quote(value)}" for key, value in media_types.items() if value])

        return (
            f"data:{file.mime_type};{media_types};base64,{buffer}"
            if media_types != ""
            else f"data:{file.mime_type};base64,{buffer}"
        )
