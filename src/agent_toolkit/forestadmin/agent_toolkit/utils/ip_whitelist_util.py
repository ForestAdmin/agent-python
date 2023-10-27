from ipaddress import ip_address, ip_network
from typing import Any, Dict

from forestadmin.datasource_toolkit.exceptions import ForestException


class IpWhitelistUtil:
    RULE_MATCH_IP = 0
    RULE_MATCH_RANGE = 1
    RULE_MATCH_SUBNET = 2

    @staticmethod
    def is_ip_match_rule(ip: str, rule: Dict[str, Any]):
        if rule["type"] == IpWhitelistUtil.RULE_MATCH_IP:
            return IpWhitelistUtil.is_ip_match_ip(ip, rule["ip"])
        elif rule["type"] == IpWhitelistUtil.RULE_MATCH_RANGE:
            return IpWhitelistUtil.is_ip_match_range(ip, rule["ipMinimum"], rule["ipMaximum"])
        elif rule["type"] == IpWhitelistUtil.RULE_MATCH_SUBNET:
            return IpWhitelistUtil.is_ip_match_subnet(ip, rule["range"])
        else:
            raise ForestException("Invalid rule type")

    @staticmethod
    def is_ip_match_ip(ip1: str, ip2: str):
        if not IpWhitelistUtil.is_same_ip_version(ip1, ip2):
            return IpWhitelistUtil.is_both_loopback(ip1, ip2)

        if ip1 == ip2:
            return True
        else:
            return IpWhitelistUtil.is_both_loopback(ip1, ip2)

    @staticmethod
    def is_same_ip_version(ip1: str, ip2: str):
        return ip_address(ip1).version == ip_address(ip2).version

    @staticmethod
    def is_both_loopback(ip1: str, ip2: str):
        return ip_address(ip1).is_loopback and ip_address(ip2).is_loopback

    @staticmethod
    def is_ip_match_range(ip: str, min_: str, max_: str):
        if not IpWhitelistUtil.is_same_ip_version(ip, min_):
            return False

        return ip_address(ip) >= ip_address(min_) and ip_address(ip) <= ip_address(max_)

    @staticmethod
    def is_ip_match_subnet(ip: str, subnet: str):
        if not IpWhitelistUtil.is_same_ip_version(ip, str(ip_network(subnet).hosts().__next__())):
            return False

        return ip_address(ip) in ip_network(subnet)
