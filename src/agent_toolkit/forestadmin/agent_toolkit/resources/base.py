from abc import abstractmethod
from typing import Any, Union

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, Response


class BaseResource:
    def __init__(self, options: Options):
        self.option = options

    @abstractmethod
    async def dispatch(self, request: Request, method_name: Any) -> Union[Response, FileResponse]:
        """must be overridden by each subclass"""
