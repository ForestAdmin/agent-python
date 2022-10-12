from abc import abstractmethod
from typing import Any

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.utils.context import Request, Response


class BaseResource:
    def __init__(self, options: Options):
        self.option = options

    @abstractmethod
    async def dispatch(self, request: Request, method_name: Any) -> Response:
        pass
