from typing import Any

from cachetools import TTLCache
from forestadmin.agent_toolkit.services.permissions.options import RoleOptions
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.agent_toolkit.utils.ip_whitelist_util import IpWhitelistUtil
from forestadmin.datasource_toolkit.exceptions import ForestException


class IpWhiteListService:
    def __init__(self, options: RoleOptions) -> None:
        self._options = options
        self.cache: TTLCache[int, Any] = TTLCache(maxsize=256, ttl=options["permission_cache_duration"])

    def invalidate_cache(self):
        for key in ["rules", "use_ip_whitelist"]:
            if key in self.cache:
                del self.cache[key]

    async def retrieve(self):
        try:
            response = await ForestHttpApi.get_ip_white_list_rules(self._options)
        except Exception as exc:
            raise ForestException(str(exc))

        ip_whitelist_data = response["data"]["attributes"]
        self.invalidate_cache()
        self.cache["use_ip_whitelist"] = ip_whitelist_data["use_ip_whitelist"]
        self.cache["rules"] = ip_whitelist_data["rules"]

    async def is_enable(self):
        if "rules" not in self.cache or "use_ip_whitelist" not in self.cache:
            await self.retrieve()
        return self.cache["use_ip_whitelist"] is True and len(self.cache["rules"]) > 0

    async def is_ip_match_any_rule(self, ip: str):
        if "rules" not in self.cache or "use_ip_whitelist" not in self.cache:
            await self.retrieve()

        for rule in self.cache["rules"]:
            if IpWhitelistUtil.is_ip_match_rule(ip, rule):
                return True

        return False
