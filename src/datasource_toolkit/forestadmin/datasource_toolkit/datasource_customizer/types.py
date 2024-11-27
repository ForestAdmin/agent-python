from typing import Dict, List, Union

from forestadmin.datasource_toolkit.decorators.rename_collection.datasource import RenameCollectionHandler
from typing_extensions import NotRequired, TypedDict


class DataSourceOptions(TypedDict):
    rename: NotRequired[Union[Dict[str, str], RenameCollectionHandler]]
    include: NotRequired[List[str]]
    exclude: NotRequired[List[str]]
