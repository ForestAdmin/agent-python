from typing import List, Literal, Union, cast

from forestadmin.agent_toolkit.utils.forest_schema.action_values import ForestValueConverter
from forestadmin.agent_toolkit.utils.forest_schema.generator_action_field_widget import GeneratorActionFieldWidget
from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import ForestServerAction, ForestServerActionField
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasource_customizer.collection_customizer import CollectionCustomizer
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import Action, ActionField, ActionFieldType
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaActionGenerator:
    DUMMY_FIELDS = [
        ForestServerActionField(
            field="Loading...",
            type=SchemaFieldGenerator.build_column_type(PrimitiveType.STRING),
            isReadOnly=True,
            defaultValue="Form is loading",
            value=None,
            description="",
            enums=None,
            hook=None,
            isRequired=False,
            reference=None,
            widgetEdit=None,
        )
    ]

    @classmethod
    async def build(
        cls, prefix: str, collection: Union[Collection, CollectionCustomizer], name: str
    ) -> ForestServerAction:
        schema = collection.schema["actions"][name]
        idx = list(collection.schema["actions"].keys()).index(name)
        slug = name.lower().replace(r"[^a-z0-9-]+", "-")
        return ForestServerAction(
            id=f"{collection.name}-{idx}-{slug}",
            name=name,
            type=cast(Literal["single", "bulk", "global"], schema.scope.value.lower()),
            endpoint=f"/forest/_actions/{collection.name}/{idx}/{slug}",
            download=bool(schema.generate_file),
            fields=await cls.build_fields(collection, schema, name),
            # Always registering the change hook has no consequences, even if we don't use it.
            hooks={"load": not schema.static_form, "change": ["changeHook"]},
        )

    @classmethod
    async def build_field_schema(
        cls, datasource: Datasource[Collection], field: ActionField
    ) -> ForestServerActionField:
        value = ForestValueConverter.value_to_forest(field, field["value"])
        default_value = ForestValueConverter.value_to_forest(field, field["default_value"])
        output: ForestServerActionField = {
            "field": field["label"],
            "value": value,
            # When sending to server, we need to rename 'value' into 'defaultValue'
            # otherwise, it does not gets applied 🤷‍♂️
            "defaultValue": default_value,
            "description": field.get("description"),
            "enums": None,
            "hook": None,
            "isReadOnly": field.get("is_read_only", False),
            "isRequired": field.get("is_required", True),
            "reference": None,
            "type": PrimitiveType.STRING,
            "widgetEdit": GeneratorActionFieldWidget.build_widget_options(field),  # type:ignore
        }
        if field["type"] == ActionFieldType.COLLECTION:
            collection: Collection = datasource.get_collection(field["collection_name"])  # type: ignore
            pk = SchemaUtils.get_primary_keys(collection.schema)[0]
            pk_schema = cast(Column, collection.get_field(pk))
            output["type"] = SchemaFieldGenerator.build_column_type(pk_schema["column_type"])  # type: ignore
            output["reference"] = f"{collection.name}.{pk}"

        elif "File" in field["type"].value:
            output["type"] = ["File"] if "List" in field["type"].value else "File"

        elif field["type"].value.endswith("List"):
            output["type"] = [PrimitiveType(field["type"].value[:-4])]
        else:
            output["type"] = field["type"].value

        if field["type"] in [ActionFieldType.ENUM, ActionFieldType.ENUM_LIST]:
            output["enums"] = field["enum_values"]

        if not isinstance(output["type"], str):
            output["type"] = SchemaFieldGenerator.build_column_type(output["type"])

        if field["watch_changes"]:
            output["hook"] = "changeHook"

        return ForestServerActionField(**output)

    @classmethod
    async def build_fields(
        cls, collection: Union[Collection, CollectionCustomizer], action: Action, name: str
    ) -> List[ForestServerActionField]:
        if not action.static_form:
            return cls.DUMMY_FIELDS
        fields = await collection.get_form(None, name, None, None)
        new_fields: List[ForestServerActionField] = []
        for field in fields:
            new_fields.append(await cls.build_field_schema(collection.datasource, field))
        return new_fields
