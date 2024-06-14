from typing import Dict, List

from typing_extensions import NotRequired, TypedDict


class DataSourceOptions(TypedDict):
    rename: NotRequired[Dict[str, str]]
    # TODO: rename should also be a function
    include: NotRequired[List[str]]
    exclude: NotRequired[List[str]]
