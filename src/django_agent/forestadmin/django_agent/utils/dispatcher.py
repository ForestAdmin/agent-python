from typing import Union

from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudLiteralMethod
from forestadmin.agent_toolkit.resources.collections.crud import LiteralMethod as CrudRelatedLiteralMethod

LiteralMethod = Union[CrudLiteralMethod, CrudRelatedLiteralMethod]

# All this file is duplicated

LIST_MAPPER = {
    "LIST": {
        "GET": "list",
        "POST": "add",
        "DELETE": "delete_list",
        "PUT": "update_list",  # useful for the related resources
    },
    "DETAIL": {"GET": "get", "PUT": "update", "DELETE": "delete"},
}


def get_dispatcher_method(request_method: str, detail: bool = False) -> LiteralMethod:
    key = "LIST"
    if detail:
        key = "DETAIL"
    return LIST_MAPPER[key][request_method]
