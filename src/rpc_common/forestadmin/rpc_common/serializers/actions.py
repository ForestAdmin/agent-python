from base64 import b64decode, b64encode
from io import IOBase

from forestadmin.datasource_toolkit.collections import Collection
from forestadmin.datasource_toolkit.interfaces.actions import (
    ActionFieldType,
    ActionResult,
    ActionsScope,
    ErrorResult,
    File,
    FileResult,
    RedirectResult,
    SuccessResult,
    WebHookResult,
)
from forestadmin.rpc_common.serializers.utils import enum_to_str_or_value


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
            "scope": action.scope.value.lower(),
            "is_generate_file": action.generate_file or False,
            "static_form": action.static_form or False,
            "description": action.description,
            "submit_button_label": action.submit_button_label,
            "form": ActionFormSerializer.serialize(form) if form is not None else [],
            "execute": {},  # TODO: I'm pretty sure this is not needed
        }

    @staticmethod
    def deserialize(action: dict) -> dict:
        return {
            "scope": ActionsScope(action["scope"].capitalize()),
            "generate_file": action["is_generate_file"],
            "static_form": action["static_form"],
            "description": action["description"],
            "submit_button_label": action["submit_button_label"],
            "form": ActionFormSerializer.deserialize(action["form"]) if action["form"] is not None else [],
        }


class ActionFormSerializer:
    @staticmethod
    def serialize(form) -> list[dict]:
        serialized_form = []

        for field in form:
            tmp_field = {}
            if field["type"] == ActionFieldType.LAYOUT:
                if field["component"] == "Page":
                    tmp_field = {
                        **field,
                        "type": "Layout",
                        "elements": ActionFormSerializer.serialize(field["elements"]),
                    }

                if field["component"] == "Row":
                    tmp_field = {
                        **field,
                        "type": "Layout",
                        "fields": ActionFormSerializer.serialize(field["fields"]),
                    }
            else:
                tmp_field = {
                    **{k: v for k, v in field.items()},
                    "type": enum_to_str_or_value(field["type"]),
                }
                if field["type"] == ActionFieldType.FILE:
                    tmp_field.update(ActionFormSerializer._serialize_file_field(tmp_field))
                if field["type"] == ActionFieldType.FILE_LIST:
                    tmp_field.update(ActionFormSerializer._serialize_file_list_field(tmp_field))

            if "if_" in tmp_field:
                tmp_field["if_condition"] = tmp_field["if_"]
                del tmp_field["if_"]
            serialized_form.append(tmp_field)

        return serialized_form

    @staticmethod
    def _serialize_file_list_field(field: dict) -> dict:
        ret = {}
        if field.get("defaultValue"):
            ret["defaultValue"] = [ActionFormSerializer._serialize_file_obj(v) for v in field["defaultValue"]]
        if field.get("value"):
            ret["value"] = [ActionFormSerializer._serialize_file_obj(v) for v in field["value"]]
        return ret

    @staticmethod
    def _serialize_file_field(field: dict) -> dict:
        ret = {}
        if field.get("defaultValue"):
            ret["defaultValue"] = ActionFormSerializer._serialize_file_obj(field["defaultValue"])
        if field.get("value"):
            ret["value"] = ActionFormSerializer._serialize_file_obj(field["value"])

    @staticmethod
    def _serialize_file_obj(f: File) -> dict:
        return {
            "mimeType": f.mime_type,
            "name": f.name,
            "stream": b64encode(f.buffer).decode("utf-8"),
            "charset": f.charset,
        }

    @staticmethod
    def _deserialize_file_obj(f: dict) -> File:
        return File(
            mime_type=f["mimeType"],
            name=f["name"],
            buffer=b64decode(f["stream"].encode("utf-8")),
            charset=f["charset"],
        )

    @staticmethod
    def _deserialize_file_field(field: dict) -> dict:
        ret = {}
        if field.get("default_value"):
            ret["default_value"] = ActionFormSerializer._deserialize_file_obj(field["default_value"])
        if field.get("value"):
            ret["value"] = ActionFormSerializer._deserialize_file_obj(field["value"])
        return ret

    @staticmethod
    def _deserialize_file_list_field(field: dict) -> dict:
        ret = {}
        if field.get("default_value"):
            ret["default_value"] = [ActionFormSerializer._deserialize_file_obj(v) for v in field["default_value"]]
        if field.get("value"):
            ret["value"] = [ActionFormSerializer._deserialize_file_obj(v) for v in field["value"]]
        return ret

    @staticmethod
    def deserialize(form: list) -> list[dict]:
        deserialized_form = []

        for field in form:
            tmp_field = {}
            if field["type"] == "Layout":
                if field["component"] == "Page":
                    tmp_field = {
                        **field,
                        "type": ActionFieldType("Layout"),
                        "elements": ActionFormSerializer.deserialize(field["elements"]),
                    }

                if field["component"] == "Row":
                    tmp_field = {
                        **field,
                        "type": ActionFieldType("Layout"),
                        "fields": ActionFormSerializer.deserialize(field["fields"]),
                    }
            else:
                tmp_field = {
                    **{k: v for k, v in field.items()},
                    "type": ActionFieldType(field["type"]),
                }
                if tmp_field["type"] == ActionFieldType.FILE:
                    tmp_field.update(ActionFormSerializer._deserialize_file_field(tmp_field))
                if tmp_field["type"] == ActionFieldType.FILE_LIST:
                    tmp_field.update(ActionFormSerializer._deserialize_file_list_field(tmp_field))

            if "if_condition" in tmp_field:
                tmp_field["if_"] = tmp_field["if_condition"]
                del tmp_field["if_condition"]
            deserialized_form.append(tmp_field)

        return deserialized_form


class ActionFormValuesSerializer:
    @staticmethod
    def serialize(form_values: dict) -> dict:
        if form_values is None:
            return {}
        ret = {}
        for key, value in form_values.items():
            if isinstance(value, File):
                ret[key] = ActionFormSerializer._serialize_file_obj(value)
            elif isinstance(value, list) and all(isinstance(v, File) for v in value):
                ret[key] = [ActionFormSerializer._serialize_file_obj(v) for v in value]
            else:
                ret[key] = value
        return ret

    @staticmethod
    def deserialize(form_values: dict) -> dict:
        ret = {}
        for key, value in form_values.items():
            if isinstance(value, dict) and "mimeType" in value:
                ret[key] = ActionFormSerializer._deserialize_file_obj(value)
            elif isinstance(value, list) and all(isinstance(v, dict) and "mimeType" in v for v in value):
                ret[key] = [ActionFormSerializer._deserialize_file_obj(v) for v in value]
            else:
                ret[key] = value
        return ret


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
