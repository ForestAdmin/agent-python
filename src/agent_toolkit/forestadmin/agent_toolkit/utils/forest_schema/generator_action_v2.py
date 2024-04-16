from typing import List, Union, cast

from forestadmin.agent_toolkit.utils.forest_schema.action_values import ForestValueConverter
from forestadmin.agent_toolkit.utils.forest_schema.generator_action_field_widget import GeneratorActionFieldWidget
from forestadmin.agent_toolkit.utils.forest_schema.generator_field_v2 import SchemaFieldGeneratorV2
from forestadmin.agent_toolkit.utils.forest_schema.type_v2 import SchemaV2Action, SchemaV2ActionField
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionField, ActionFieldType
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaActionGeneratorV2:
    @classmethod
    async def build(cls, prefix: str, collection: Union[Collection, CollectionCustomizer], name: str) -> SchemaV2Action:
        schema = collection.schema["actions"][name]
        idx = list(collection.schema["actions"].keys()).index(name)
        slug = name.lower().replace(r"[^a-z0-9-]+", "-")
        ret = SchemaV2Action(
            id=f"{collection.name}-{idx}-{slug}",  # type:ignore
            name=name,
            scope=schema.scope.value.lower(),  # type:ignore
            endpoint=f"/forest/_actions/{collection.name}/{idx}/{slug}",  # type:ignore
            download=bool(schema.generate_file),
            isDynamicForm=not schema.static_form,
        )
        if schema.static_form:
            ret["fields"] = await cls.build_fields(collection, schema, name)

        return ret

    @classmethod
    async def build_field_schema(cls, datasource: Datasource[Collection], field: ActionField) -> SchemaV2ActionField:
        value = ForestValueConverter.value_to_forest(field, field.get("value"))
        default_value = ForestValueConverter.value_to_forest(field, field.get("default_value"))
        output: SchemaV2ActionField = {
            "name": field["label"],
            "type": field["type"],
            "description": field.get("description"),
            # When sending to server, we need to rename 'value' into 'defaultValue'
            # otherwise, it does not gets applied 🤷‍♂️
            "value": value,
            "prefillValue": default_value,
            # "enumeration": None,  # default value
            "isReadOnly": (
                field["is_read_only"] if "is_read_only" in field and field["is_read_only"] is not None else False
            ),
            "isRequired": (
                field["is_required"] if "is_required" in field and field["is_required"] is not None else True
            ),
            # "reference": None,  # default value
            "widget": GeneratorActionFieldWidget.build_widget_options(field),
        }
        if field["type"] == ActionFieldType.COLLECTION:
            collection: Collection = datasource.get_collection(field["collection_name"])  # type: ignore
            pk = SchemaUtils.get_primary_keys(collection.schema)[0]
            pk_schema = cast(Column, collection.get_field(pk))
            output["type"] = SchemaFieldGeneratorV2.build_column_type(pk_schema["column_type"])  # type: ignore
            output["reference"] = f"{collection.name}.{pk}"

        elif "File" in field["type"].value:
            output["type"] = ["File"] if "List" in field["type"].value else "File"  # type: ignore

        elif field["type"].value.endswith("List"):
            output["type"] = [PrimitiveType(field["type"].value[:-4])]  # type: ignore
        else:
            output["type"] = field["type"].value  # type: ignore

        if field["type"] in [ActionFieldType.ENUM, ActionFieldType.ENUM_LIST]:
            output["enumeration"] = field.get("enum_values")

        if not isinstance(output["type"], str):
            output["type"] = SchemaFieldGeneratorV2.build_column_type(output["type"])  # type: ignore

        return SchemaV2ActionField(**output)

    @classmethod
    async def build_fields(
        cls, collection: Union[Collection, CollectionCustomizer], action: Action, name: str
    ) -> List[SchemaV2ActionField]:
        fields = await collection.get_form(None, name, None, None)  # type:ignore
        new_fields: List[SchemaV2ActionField] = []
        for field in fields:
            new_fields.append(await cls.build_field_schema(collection.datasource, field))  # type:ignore
        return new_fields
