from typing import List, Literal, Tuple, cast

from forestadmin.agent_toolkit.exceptions import AgentToolkitException
from forestadmin.agent_toolkit.utils.forest_schema.action_values import ForestValueConverter
from forestadmin.agent_toolkit.utils.forest_schema.generator_action_field_widget import GeneratorActionFieldWidget
from forestadmin.agent_toolkit.utils.forest_schema.generator_field import SchemaFieldGenerator
from forestadmin.agent_toolkit.utils.forest_schema.type import (
    ForestServerAction,
    ForestServerActionField,
    ForestServerActionFormLayoutElement,
)
from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.datasources import Datasource
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionField,
    ActionFieldType,
    ActionFormElement,
    ActionLayoutElement,
)
from forestadmin.datasource_toolkit.interfaces.fields import Column, PrimitiveType
from forestadmin.datasource_toolkit.utils.schema import SchemaUtils


class SchemaActionGenerator:
    DUMMY_FIELDS = [
        ForestServerActionField(
            field="Loading...",
            label="Loading...",
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
    async def build(cls, prefix: str, collection: Collection, name: str) -> ForestServerAction:
        schema = collection.schema["actions"][name]
        idx = list(collection.schema["actions"].keys()).index(name)
        slug = name.lower().replace(r"[^a-z0-9-]+", "-")

        if not schema.static_form:
            fields, layout = (cls.DUMMY_FIELDS, [])
        else:
            form = await collection.get_form(None, name, None, None)
            fields, layout = SchemaActionGenerator.extract_fields_and_layout(form)
            fields = [await SchemaActionGenerator.build_field_schema(collection.datasource, field) for field in fields]

        ret = ForestServerAction(
            id=f"{collection.name}-{idx}-{slug}",
            name=name,
            description=schema.description,
            type=cast(Literal["single", "bulk", "global"], schema.scope.value.lower()),
            endpoint=f"/forest/_actions/{collection.name}/{idx}/{slug}",
            download=bool(schema.generate_file),
            fields=fields,
            submitButtonLabel=schema.submit_button_label,
            # Always registering the change hook has no consequences, even if we don't use it.
            hooks={"load": not schema.static_form, "change": ["changeHook"]},
        )

        # when there is not layout customizations, don't send the 'layout' property
        if any([item["component"] != "Input" for item in layout]):
            ret["layout"] = [await SchemaActionGenerator.build_layout_schema(field) for field in layout]
        return ret

    @classmethod
    async def build_layout_schema(cls, field: ActionFormElement) -> ForestServerActionFormLayoutElement:
        field = cast(ActionLayoutElement, field)
        if field["component"] == "Input":
            return {"component": "input", "fieldId": field["fieldId"]}  # type:ignore
        elif field["component"] == "Separator":
            return {"component": "separator"}
        elif field["component"] == "HtmlBlock":
            return {"component": "htmlBlock", "content": field["content"]}  # type:ignore
        elif field["component"] == "Row":
            return {
                "component": "row",
                "fields": [await cls.build_layout_schema(f) for f in field["fields"]],  # type:ignore
            }
        elif field["component"] == "Page":
            return {
                "component": "page",
                "nextButtonLabel": field.get("next_button_label"),
                "previousButtonLabel": field.get("previous_button_label"),
                "elements": [await cls.build_layout_schema(f) for f in field["elements"]],  # type:ignore
            }
        else:
            raise AgentToolkitException(f"Unknown component '{field['component']}'")

    @classmethod
    async def build_field_schema(
        cls, datasource: Datasource[Collection], field: ActionField
    ) -> ForestServerActionField:
        value = ForestValueConverter.value_to_forest(field, field["value"])
        default_value = ForestValueConverter.value_to_forest(field, field["default_value"])
        output: ForestServerActionField = {
            "field": field["id"],
            "label": field["label"],
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
    def extract_fields_and_layout(
        cls, form_elements: List[ActionFormElement]
    ) -> Tuple[List[ActionField], List[ActionLayoutElement]]:
        fields: List[ActionField] = []
        layout: List[ActionLayoutElement] = []

        for element in form_elements:
            if element["type"] != ActionFieldType.LAYOUT:
                fields.append(cast(ActionField, element))
                layout.append(
                    {
                        "type": ActionFieldType.LAYOUT,
                        "component": "Input",
                        "fieldId": cast(ActionField, element)["id"],
                    }
                )
            else:
                if element["component"] == "Row":  # type: ignore
                    sub_fields, sub_layout = cls.extract_fields_and_layout(element["fields"])  # type: ignore
                    layout.append({**element, "fields": sub_layout})  # type: ignore
                    fields.extend(sub_fields)
                elif element["component"] == "Page":  # type: ignore
                    sub_fields, sub_layout = cls.extract_fields_and_layout(element["elements"])  # type: ignore
                    fields.extend(sub_fields)
                    layout.append({**element, "elements": sub_layout})  # type: ignore
                else:
                    layout.append(cast(ActionLayoutElement, element))

        return fields, layout
