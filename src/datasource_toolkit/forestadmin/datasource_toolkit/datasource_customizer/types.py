from typing import Callable, Dict, List, Optional, Union

from typing_extensions import NotRequired, TypedDict


class DataSourceOptions(TypedDict):
    rename: NotRequired[Optional[Union[Dict[str, str], Callable[[str], str]]]]
    include: NotRequired[Optional[List[str]]]
    exclude: NotRequired[Optional[List[str]]]
