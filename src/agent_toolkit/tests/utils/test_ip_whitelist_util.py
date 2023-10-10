from unittest import TestCase

from forestadmin.agent_toolkit.utils.ip_whitelist_util import IpWhitelistUtil


class TestIpWhiteListUtilIsIpMatchIp(TestCase):
    def test_is_ip_match_ip_should_return_true_when_same_ip(self):
        self.assertTrue(IpWhitelistUtil.is_ip_match_ip("127.0.0.1", "127.0.0.1"))
        self.assertTrue(IpWhitelistUtil.is_ip_match_ip("192.168.1.10", "192.168.1.10"))

    def test_is_ip_match_ip_should_return_true_when_same_ip_v6(self):
        self.assertTrue(IpWhitelistUtil.is_ip_match_ip("::1", "::1"))
        self.assertTrue(
            IpWhitelistUtil.is_ip_match_ip(
                "2001:0620:0000:0000:0211:24FF:FE80:C12C", "2001:0620:0000:0000:0211:24FF:FE80:C12C"
            )
        )

    def test_is_ip_match_ip_should_return_true_when_different_ip_version_but_loopback(self):
        self.assertTrue(IpWhitelistUtil.is_ip_match_ip("::1", "127.0.0.1"))

    def test_is_ip_match_ip_should_return_false_when_ips_does_not_match(self):
        self.assertFalse(IpWhitelistUtil.is_ip_match_ip("192.168.1.10", "127.0.0.1"))


class TestIpWhiteListUtilIsSameIpVersion(TestCase):
    def test_should_return_true_when_comparing_same_ip_version(self):
        self.assertTrue(IpWhitelistUtil.is_same_ip_version("::1", "2001:0620:0000:0000:0211:24FF:FE80:C12C"))
        self.assertTrue(IpWhitelistUtil.is_same_ip_version("192.168.1.10", "127.0.0.1"))

    def test_should_return_false_when_comparing_different_ip_version(self):
        self.assertFalse(IpWhitelistUtil.is_same_ip_version("::1", "127.0.0.1"))


class TestIpWhiteListUtilIsBothLoopback(TestCase):
    def test_should_return_true_when_both_ip_are_loopback(self):
        self.assertTrue(IpWhitelistUtil.is_both_loopback("127.0.0.1", "127.0.0.1"))
        self.assertTrue(IpWhitelistUtil.is_both_loopback("::1", "127.0.0.1"))
        self.assertTrue(IpWhitelistUtil.is_both_loopback("::1", "::1"))

    def test_should_return_false_when_both_ip_are_not_loopback(self):
        self.assertFalse(IpWhitelistUtil.is_both_loopback("192.168.1.1", "10.0.0.1"))
        self.assertFalse(IpWhitelistUtil.is_both_loopback("::2", "192.168.1.1"))
        self.assertFalse(IpWhitelistUtil.is_both_loopback("::2", "::2"))

    def test_should_return_false_when_one_ip_only_is_loopback(self):
        self.assertFalse(IpWhitelistUtil.is_both_loopback("192.168.1.1", "127.0.0.1"))
        self.assertFalse(IpWhitelistUtil.is_both_loopback("127.0.0.1", "192.168.1.1"))
        self.assertFalse(IpWhitelistUtil.is_both_loopback("::1", "192.168.1.1"))
        self.assertFalse(IpWhitelistUtil.is_both_loopback("::1", "::2"))


class TestIpWhiteListUtilIsIpMatchRange(TestCase):
    def test_should_return_true_when_ip_is_in_range(self):
        self.assertTrue(IpWhitelistUtil.is_ip_match_range("192.168.1.10", "192.168.1.1", "192.168.1.100"))
        self.assertTrue(
            IpWhitelistUtil.is_ip_match_range(
                "2001:0620:0000:0000:0211:24FF:FE80:C12C",
                "2001:0620:0000:0000:0211:24FF:FE80:C100",
                "2001:0620:0000:0000:0211:24FF:FE80:C1FF",
            )
        )

    def test_should_return_false_when_ip_is_not_in_range(self):
        self.assertFalse(IpWhitelistUtil.is_ip_match_range("192.168.1.100", "192.168.1.1", "192.168.1.10"))
        self.assertFalse(
            IpWhitelistUtil.is_ip_match_range(
                "2001:0620:0000:0000:0211:24FF:FE80:C12C",
                "2001:0620:0000:0000:0211:24FF:FE80:C150",
                "2001:0620:0000:0000:0211:24FF:FE80:C1FF",
            )
        )
        self.assertFalse(
            IpWhitelistUtil.is_ip_match_range("2001:0620:0000:0000:0211:24FF:FE80:C12C", "192.168.1.1", "192.168.1.10")
        )


class TestIpWhiteListUtilIsIpMatchRangeSubnet(TestCase):
    def test_should_return_true_when_ip_is_in_subnet(self):
        self.assertTrue(IpWhitelistUtil.is_ip_match_subnet("192.168.1.100", "192.168.1.0/24"))
        self.assertTrue(
            IpWhitelistUtil.is_ip_match_subnet(
                "fe80:0000:0000:0000:0211:24FF:FE80:C12C",
                "fe80:0000:0000:0000:0000:0000:0000:0000/32",
            )
        )

    def test_should_return_false_when_ip_is_not_in_subnet(self):
        self.assertFalse(IpWhitelistUtil.is_ip_match_subnet("192.168.2.100", "192.168.1.0/24"))
        self.assertFalse(
            IpWhitelistUtil.is_ip_match_subnet(
                "fe80:0001:0000:0000:0211:24FF:FE80:C12C",
                "fe80:0000:0000:0000:0000:0000:0000:0000/32",
            )
        )
        self.assertFalse(
            IpWhitelistUtil.is_ip_match_subnet("fe80:0001:0000:0000:0211:24FF:FE80:C12C", "192.168.1.0/24")
        )
