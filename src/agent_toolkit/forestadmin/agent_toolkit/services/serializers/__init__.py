from typing import Any, Dict, List, Optional, TypedDict


class Data(TypedDict):
    type: str
    relationships: Dict[str, Any]
    attributes: Dict[str, Any]
    id: int
    links: Dict[str, Any]


class DumpedResult(TypedDict):
    data: List[Data]
    included: Dict[str, Any]
    meta: Optional[Dict[str, Any]]


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
