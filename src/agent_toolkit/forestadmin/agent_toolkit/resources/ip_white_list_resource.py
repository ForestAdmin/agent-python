from typing import Union

from forestadmin.agent_toolkit.options import Options
from forestadmin.agent_toolkit.resources.base import BaseResource
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.utils.context import FileResponse, Request, Response
from forestadmin.datasource_toolkit.exceptions import ForbiddenError


class IpWhitelistResource(BaseResource):
    def __init__(self, ip_white_list_service: IpWhiteListService, options: Options):
        super().__init__(options)
        self._ip_whitelist: IpWhiteListService = ip_white_list_service

    async def check_ip(self, request: Request) -> Union[Response, FileResponse]:
        if await self._ip_whitelist.is_enable():
            ip = request.client_ip
            if not await self._ip_whitelist.is_ip_match_any_rule(ip):
                raise ForbiddenError(f"IP address rejected ({ip})")
