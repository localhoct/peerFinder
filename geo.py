import ipaddress
import requests


API_URL = "https://ipwho.is/{ip}"


def country_from_ip(ip, timeout=15):
    """Return ISO country code for an IP using ipwho.is, or UNKNOWN."""
    try:
        parsed = ipaddress.ip_address(ip)
        if parsed.is_private or parsed.is_loopback or parsed.is_reserved:
            return "UNKNOWN"

        response = requests.get(API_URL.format(ip=parsed), timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return (data.get("country_code") or "UNKNOWN").upper()
    except (ValueError, requests.RequestException, TypeError):
        return "UNKNOWN"


def country_from_peer(name):
    """Compatibility helper; country detection should use country_from_ip."""
    return "UNKNOWN"
