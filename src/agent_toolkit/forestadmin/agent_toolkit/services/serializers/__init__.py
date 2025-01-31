from typing import Any, Dict, List, Union

from typing_extensions import NotRequired, TypedDict


class Data(TypedDict):
    type: str
    id: int
    attributes: Dict[str, Any]
    relationships: Dict[str, Any]
    links: Dict[str, Any]


class IncludedData(TypedDict):
    type: str
    id: int
    links: Dict[str, Any]
    attributes: NotRequired[Dict[str, Any]]
    relationships: NotRequired[Dict[str, Any]]


class DumpedResult(TypedDict):
    data: Union[List[Data], Data]
    included: NotRequired[List[IncludedData]]
    meta: NotRequired[Dict[str, Any]]


def add_search_metadata(dumped: DumpedResult, search_value: str):
    if len(search_value.strip()) > 0:
        results_data = dumped["data"]
        decorators: Dict[int, Dict[str, Any]] = {}
        key = 0
        for result in results_data:
            search_fields: List[str] = []
            for field_name, value in result.get("attributes", {}).items():
                if search_value.lower() in str(value).lower():
                    search_fields.append(field_name)
            if len(search_fields) > 0:
                decorators[key] = {"id": result["id"], "search": search_fields}
                key += 1
        dumped["meta"] = {"decorators": decorators}
    return dumped
