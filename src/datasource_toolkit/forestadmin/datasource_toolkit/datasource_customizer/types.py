from typing import Callable, Dict, List, Optional, TypedDict, Union


class DataSourceOptions(TypedDict):
    rename: Optional[Union[Dict[str, str], Callable[[str], str]]]
    include: Optional[List[str]]
    exclude: Optional[List[str]]
