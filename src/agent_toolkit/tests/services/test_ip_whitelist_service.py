import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from forestadmin.agent_toolkit.services.permissions.ip_whitelist_service import IpWhiteListService
from forestadmin.agent_toolkit.utils.http import ForestHttpApi
from forestadmin.datasource_toolkit.exceptions import ForestException


class BaseTestIpWhiteListService(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.options = {"permission_cache_duration": 15}
        cls.loop = asyncio.new_event_loop()

    def setUp(self) -> None:
        self.ip_whitelist = IpWhiteListService(self.options)

    def get_mock_http_ip_white_list(self, rules=[], enabled=True):
        return patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
            return_value={
                "data": {
                    "type": "ip-whitelist-rules",
                    "id": "1",
                    "attributes": {
                        "rules": rules,
                        "use_ip_whitelist": enabled,
                    },
                }
            },
        )


class TestIsEnabled(BaseTestIpWhiteListService):
    def test_is_enabled_should_return_true_when_there_is_rules_and_use_ip_wl_is_true(self):
        with self.get_mock_http_ip_white_list([{"type": 0, "ip": "127.0.0.1"}]):
            self.assertEqual(self.loop.run_until_complete(self.ip_whitelist.is_enable()), True)

    def test_is_enabled_should_return_true_when_there_is_no_rules_and_use_ip_wl_is_true(self):
        with self.get_mock_http_ip_white_list([]):
            self.assertEqual(self.loop.run_until_complete(self.ip_whitelist.is_enable()), False)

    def test_is_enabled_should_return_true_when_there_is_rules_and_use_ip_wl_is_false(self):
        with self.get_mock_http_ip_white_list([{"type": 0, "ip": "127.0.0.1"}], False):
            self.assertEqual(self.loop.run_until_complete(self.ip_whitelist.is_enable()), False)

    def test_is_enabled_should_fetch_data_if_cache_expire(self):
        self.ip_whitelist.invalidate_cache()
        self.assertNotIn("use_ip_whitelist", self.ip_whitelist.cache)
        self.assertNotIn("rules", self.ip_whitelist.cache)

        with patch.object(self.ip_whitelist, "retrieve", wraps=self.ip_whitelist.retrieve) as mock_retrieve:
            with self.get_mock_http_ip_white_list([{"type": 0, "ip": "127.0.0.1"}], False):
                self.loop.run_until_complete(self.ip_whitelist.is_enable())

            mock_retrieve.assert_awaited_once()
        self.assertIn("use_ip_whitelist", self.ip_whitelist.cache)
        self.assertIn("rules", self.ip_whitelist.cache)


class TestIsIpMatchAnyRule(BaseTestIpWhiteListService):
    def test_is_ip_match_any_rules_should_return_true_when_client_ip_match_RULE_MATCH_IP(self):
        with self.get_mock_http_ip_white_list([{"type": 0, "ip": "127.0.0.1"}]):
            self.assertTrue(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("127.0.0.1")))

    def test_is_ip_match_any_rules_should_return_false_when_client_ip_not_match_RULE_MATCH_IP(self):
        with self.get_mock_http_ip_white_list([{"type": 0, "ip": "127.0.0.1"}]):
            self.assertFalse(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("192.168.1.1")))

    def test_is_ip_match_any_rules_should_return_true_when_client_ip_is_in_range(self):
        with self.get_mock_http_ip_white_list([{"type": 1, "ipMinimum": "10.0.0.1", "ipMaximum": "10.0.0.100"}]):
            self.assertTrue(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("10.0.0.44")))

    def test_is_ip_match_any_rules_should_return_false_when_client_ip_is_not_in_range(self):
        with self.get_mock_http_ip_white_list([{"type": 1, "ipMinimum": "10.0.0.1", "ipMaximum": "10.0.0.100"}]):
            self.assertFalse(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("10.0.0.144")))

    def test_is_ip_match_any_rules_should_return_true_when_client_ip_is_in_subnet(self):
        with self.get_mock_http_ip_white_list([{"type": 2, "range": "200.10.10.0/24"}]):
            self.assertTrue(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("200.10.10.20")))

    def test_is_ip_match_any_rules_should_return_false_when_client_ip_is_not_in_subnet(self):
        with self.get_mock_http_ip_white_list([{"type": 2, "range": "200.10.10.0/24"}]):
            self.assertFalse(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("10.0.0.144")))

    def test_is_ip_match_any_rules_should_return_false_when_client_ip_not_match_any_rules(self):
        with self.get_mock_http_ip_white_list(
            [
                {"type": 0, "ip": "127.0.0.1"},
                {"type": 1, "ipMinimum": "10.0.0.1", "ipMaximum": "10.0.0.100"},
                {"type": 2, "range": "200.10.10.0/24"},
            ]
        ):
            self.assertFalse(self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("200.200.100.100")))

    def test_is_ip_match_any_rules_should_raise_when_bad_rule(self):
        with self.get_mock_http_ip_white_list([{"type": 4, "range": "200.10.10.0/24"}]):
            self.assertRaisesRegex(
                ForestException,
                r"🌳🌳🌳Invalid rule type",
                self.loop.run_until_complete,
                self.ip_whitelist.is_ip_match_any_rule("200.200.100.100"),
            )

    def test_is_ip_match_any_rules_should_fetch_data_if_cache_expire(self):
        self.ip_whitelist.invalidate_cache()
        self.assertNotIn("use_ip_whitelist", self.ip_whitelist.cache)
        self.assertNotIn("rules", self.ip_whitelist.cache)

        with patch.object(self.ip_whitelist, "retrieve", wraps=self.ip_whitelist.retrieve) as mock_retrieve:
            with self.get_mock_http_ip_white_list([{"type": 1, "ipMinimum": "10.0.0.1", "ipMaximum": "10.0.0.100"}]):
                self.loop.run_until_complete(self.ip_whitelist.is_ip_match_any_rule("10.0.0.144"))

            mock_retrieve.assert_awaited_once()
        self.assertIn("use_ip_whitelist", self.ip_whitelist.cache)
        self.assertIn("rules", self.ip_whitelist.cache)


class TestOtherMethods(BaseTestIpWhiteListService):
    def test_call_to_retrieve_should_call_forest_http_api(self):
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
        ) as mock_get_ip_white_list:
            self.loop.run_until_complete(self.ip_whitelist.retrieve())
            mock_get_ip_white_list.assert_awaited_once_with({"permission_cache_duration": 15})

    def test_call_to_retrieve_should_call_invalidate_cache_after_fetching_data(self):
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
        ):
            with patch.object(
                self.ip_whitelist,
                "invalidate_cache",
            ) as mock_invalidate_cache:
                self.loop.run_until_complete(self.ip_whitelist.retrieve())
                mock_invalidate_cache.assert_called_once()

    def test_call_to_retrieve_should_raise_if_forest_backend_not_available(self):
        with patch.object(
            ForestHttpApi,
            "get_ip_white_list_rules",
            new_callable=AsyncMock,
            side_effect=Exception("backend not available"),
        ):
            self.assertRaisesRegex(
                ForestException, r"🌳🌳🌳backend not available", self.loop.run_until_complete, self.ip_whitelist.retrieve()
            )
