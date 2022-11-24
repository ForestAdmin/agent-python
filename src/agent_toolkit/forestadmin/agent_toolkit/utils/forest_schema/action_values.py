from typing import Any, Dict, List, cast

from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerActionField
from forestadmin.agent_toolkit.utils.id import unpack_id
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException
from forestadmin.datasource_toolkit.interfaces.actions import ActionField, ActionFieldType
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
            elif field["type"] == ActionFieldType.FILE:
                pass
            else:
                form_data[field["field"]] = field["value"]
        return form_data

    @staticmethod
    def make_form_unsafe_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        return raw_data

    @staticmethod
    def make_form_data(
        datasource: Datasource[Collection], raw_data: Dict[str, Any], fields: List[ActionField]
    ) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for key, value in raw_data.items():
            field: ActionField = list(filter(lambda f: f["label"] == key, fields))[0]  # type: ignore
            if field["type"] == ActionFieldType.COLLECTION and value:
                collection = datasource.get_collection(cast(str, field["collection_name"]))
                data[key] = unpack_id(collection.schema, value)
            elif field["type"] == ActionFieldType.FILE:
                data[key] = ""
            else:
                data[key] = value
        return data

    @staticmethod
    def value_to_forest(field: ActionField, value: Any) -> Any:
        if field["type"] == ActionFieldType.ENUM:
            if not field["enum_values"] or ((value is not None) and value not in field["enum_values"]):
                raise ForestValueConverterException(f"{value} is not in {field['enum_values']}")
            return value

        elif field["type"] == ActionFieldType.ENUM_LIST:
            for v in cast(List[str], value):
                if not field["enum_values"] or v not in field["enum_values"]:
                    raise ForestValueConverterException(f"{v} is not in {field['enum_values']}")
            return value
        elif field["type"] == ActionFieldType.COLLECTION:
            value = cast(CompositeIdAlias, value)
            return "|".join(value)

        return value
