from base64 import b64decode, b64encode
from io import IOBase

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionFieldType,
    ActionResult,
    ActionsScope,
    ErrorResult,
    FileResult,
    RedirectResult,
    SuccessResult,
    WebHookResult,
)
from forestadmin.rpc_common.serializers.utils import camel_to_snake_case, enum_to_str_or_value, snake_to_camel_case


class ActionSerializer:
    @staticmethod
    async def serialize(action_name: str, collection: Collection) -> dict:
        action = collection.schema["actions"][action_name]
        if not action.static_form:
            form = None
        else:
            # TODO: a dummy field here ??
            form = await collection.get_form(None, action_name, None, None)  # type:ignore
            # fields, layout = SchemaActionGenerator.extract_fields_and_layout(form)
            # fields = [
            #     await SchemaActionGenerator.build_field_schema(collection.datasource, field) for field in fields
            # ]

        return {
            "scope": action.scope.value,
            "generateFile": action.generate_file or False,
            "staticForm": action.static_form or False,
            "description": action.description,
            "submitButtonLabel": action.submit_button_label,
            "form": ActionFormSerializer.serialize(form) if form is not None else [],
        }

    @staticmethod
    def deserialize(action: dict) -> dict:
        return {
            "scope": ActionsScope(action["scope"]),
            "generate_file": action["generateFile"],
            "static_form": action["staticForm"],
            "description": action["description"],
            "submit_button_label": action["submitButtonLabel"],
            "form": ActionFormSerializer.deserialize(action["form"]) if action["form"] is not None else [],
        }


class ActionFormSerializer:
    @staticmethod
    def serialize(form) -> list[dict]:
        serialized_form = []

        for field in form:
            if field["type"] == ActionFieldType.LAYOUT:
                if field["component"] == "Page":
                    serialized_form.append(
                        {
                            **field,
                            "type": "Layout",
                            "elements": ActionFormSerializer.serialize(field["elements"]),
                        }
                    )

                if field["component"] == "Row":
                    serialized_form.append(
                        {
                            **field,
                            "type": "Layout",
                            "fields": ActionFormSerializer.serialize(field["fields"]),
                        }
                    )
            else:
                serialized_form.append(
                    {
                        **{snake_to_camel_case(k): v for k, v in field.items()},
                        "type": enum_to_str_or_value(field["type"]),
                    }
                )

        return serialized_form

    @staticmethod
    def deserialize(form: list) -> list[dict]:
        deserialized_form = []

        for field in form:
            if field["type"] == "Layout":
                if field["component"] == "Page":
                    deserialized_form.append(
                        {
                            **field,
                            "type": ActionFieldType("Layout"),
                            "elements": ActionFormSerializer.deserialize(field["elements"]),
                        }
                    )

                if field["component"] == "Row":
                    deserialized_form.append(
                        {
                            **field,
                            "type": ActionFieldType("Layout"),
                            "fields": ActionFormSerializer.deserialize(field["fields"]),
                        }
                    )
            else:
                deserialized_form.append(
                    {
                        **{camel_to_snake_case(k): v for k, v in field.items()},
                        "type": ActionFieldType(field["type"]),
                    }
                )

        return deserialized_form


class ActionResultSerializer:
    @staticmethod
    def serialize(action_result: dict) -> dict:
        ret = {
            "type": action_result["type"],
            "response_headers": action_result["response_headers"],
        }
        match action_result["type"]:
            case "Success":
                ret.update(
                    {
                        "message": action_result["message"],
                        "format": action_result["format"],
                        "invalidated": list(action_result["invalidated"]),
                    }
                )
            case "Error":
                ret.update({"message": action_result["message"], "format": action_result["format"]})
            case "Webhook":
                ret.update(
                    {
                        "url": action_result["url"],
                        "method": action_result["method"],
                        "headers": action_result["headers"],
                        "body": action_result["body"],
                    }
                )
            case "File":
                b64_encoded = False
                content = action_result["stream"]
                if isinstance(content, IOBase):
                    content = content.read()
                if isinstance(content, bytes):
                    content = b64encode(content).decode("utf-8")
                    b64_encoded = True
                ret.update(
                    {
                        "mimeType": action_result["mimeType"],
                        "name": action_result["name"],
                        "stream": content,
                        "b64Encoded": b64_encoded,
                    }
                )
            case "Redirect":
                ret.update({"path": action_result["path"]})
        return ret

    @staticmethod
    def deserialize(action_result: dict) -> ActionResult:
        match action_result["type"]:
            case "Success":
                return SuccessResult(
                    type="Success",
                    message=action_result["message"],
                    format=action_result["format"],
                    invalidated=set(action_result["invalidated"]),
                    response_headers=action_result["response_headers"],
                )
            case "Error":
                return ErrorResult(
                    type="Error",
                    message=action_result["message"],
                    format=action_result["format"],
                    response_headers=action_result["response_headers"],
                )
            case "Webhook":
                return WebHookResult(
                    type="Webhook",
                    url=action_result["url"],
                    method=action_result["method"],
                    headers=action_result["headers"],
                    body=action_result["body"],
                    response_headers=action_result["response_headers"],
                )
            case "File":
                stream = action_result["stream"]
                if action_result["b64Encoded"]:
                    stream = b64decode(stream.encode("utf-8"))
                return FileResult(
                    type="File",
                    mimeType=action_result["mimeType"],
                    name=action_result["name"],
                    stream=stream,
                    response_headers=action_result["response_headers"],
                )
            case "Redirect":
                return RedirectResult(
                    type="Redirect",
                    path=action_result["path"],
                    response_headers=action_result["response_headers"],
                )
            case _:
                raise ValueError(f"Invalid action result type: {action_result['type']}")
