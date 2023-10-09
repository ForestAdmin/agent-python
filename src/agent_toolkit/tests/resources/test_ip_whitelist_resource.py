import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from forestadmin.agent_toolkit.resources.ip_white_list_resource import IpWhitelistResource
from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.utils.context import Request, RequestMethod
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.exceptions import ForbiddenError


class TestIpWhitelistResource(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()
        cls.options = {
            "env_secret": "env_secret",
            "forest_server_url": "https://api.forest.com",
            "permission_cache_duration": 15,
        }

    def setUp(self) -> None:
        ip_white_list_service = IpWhiteListService(self.options)
        self.ip_whitelist_resource = IpWhitelistResource(ip_white_list_service, self.options)

    def test_check_ip_should_check_ip_rules_only_if_it_is_enabled(self):
        request = Request(RequestMethod.GET, client_ip="127.0.0.1")
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
            return_value={
                "data": {
                    "type": "ip-whitelist-rules",
                    "id": "1",
                    "attributes": {
                        "rules": [],
                        "use_ip_whitelist": False,
                    },
                }
            },
        ):
            self.loop.run_until_complete(self.ip_whitelist_resource._ip_whitelist.retrieve())

        # disable
        with patch.object(
            self.ip_whitelist_resource._ip_whitelist,
            "is_ip_match_any_rule",
            wraps=self.ip_whitelist_resource._ip_whitelist.is_ip_match_any_rule,
        ) as mock_match_rule:
            self.loop.run_until_complete(self.ip_whitelist_resource.check_ip(request))
            mock_match_rule.assert_not_called()

        # enable but no rules
        self.ip_whitelist_resource._ip_whitelist.cache["use_ip_whitelist"] = True
        with patch.object(
            self.ip_whitelist_resource._ip_whitelist,
            "is_ip_match_any_rule",
            wraps=self.ip_whitelist_resource._ip_whitelist.is_ip_match_any_rule,
        ) as mock_match_rule:
            self.loop.run_until_complete(self.ip_whitelist_resource.check_ip(request))
            mock_match_rule.assert_not_called()

        # enable with rules
        self.ip_whitelist_resource._ip_whitelist.cache["rules"] = [{"type": 0, "ip": "127.0.0.1"}]
        with patch.object(
            self.ip_whitelist_resource._ip_whitelist,
            "is_ip_match_any_rule",
            wraps=self.ip_whitelist_resource._ip_whitelist.is_ip_match_any_rule,
        ) as mock_match_rule:
            self.loop.run_until_complete(self.ip_whitelist_resource.check_ip(request))
            mock_match_rule.assert_called()

    def test_check_ip_should_raise_when_ip_not_pass_rules(self):
        request = Request(RequestMethod.GET, client_ip="192.168.1.10")
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
            return_value={
                "data": {
                    "type": "ip-whitelist-rules",
                    "id": "1",
                    "attributes": {
                        "rules": [{"type": 0, "ip": "127.0.0.1"}],
                        "use_ip_whitelist": True,
                    },
                }
            },
        ):
            self.assertRaisesRegex(
                ForbiddenError,
                r"IP address rejected \(192.168.1.10\)",
                self.loop.run_until_complete,
                self.ip_whitelist_resource.check_ip(request),
            )

    def test_check_ip_should_not_raise_when_ip_pass_rules(self):
        request = Request(RequestMethod.GET, client_ip="127.0.0.1")
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
            return_value={
                "data": {
                    "type": "ip-whitelist-rules",
                    "id": "1",
                    "attributes": {
                        "rules": [{"type": 0, "ip": "127.0.0.1"}],
                        "use_ip_whitelist": True,
                    },
                }
            },
        ):
            self.loop.run_until_complete(
                self.ip_whitelist_resource.check_ip(request),
            )
