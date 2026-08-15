from bs4 import BeautifulSoup
import ipaddress
import re

AS_RE = re.compile(r"AS(\d+)", re.I)


def extract_peers(html):
    soup = BeautifulSoup(html, "html.parser")
    peers = []
    for row in soup.find_all("tr"):
        cols = [c.get_text(" ", strip=True) for c in row.find_all("td")]
        if not cols:
            continue
        match = AS_RE.search(" ".join(cols))
        if not match:
            continue
        asn = "AS" + match.group(1)
        name = cols[1] if len(cols) > 1 else asn
        peers.append({"asn": asn, "name": name})
    unique = {}
    for peer in peers:
        unique[peer["asn"]] = peer
    return list(unique.values())


def extract_subnets(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    candidates = re.findall(r"(?<![A-Za-z0-9:])(?:[0-9A-Fa-f:.]+)/(?:[0-9]{1,3})(?![A-Za-z0-9])", text)
    result = set()
    for candidate in candidates:
        try:
            result.add(str(ipaddress.ip_network(candidate, strict=False)))
        except ValueError:
            continue
    return sorted(result, key=lambda x: (ipaddress.ip_network(x).version, int(ipaddress.ip_network(x).network_address), ipaddress.ip_network(x).prefixlen))


def split_subnets(subnets):
    ipv4, ipv6 = [], []
    for subnet in subnets:
        (ipv4 if ipaddress.ip_network(subnet).version == 4 else ipv6).append(subnet)
    return ipv4, ipv6


def representative_ip(subnets):
    for subnet in subnets:
        network = ipaddress.ip_network(subnet)
        if network.version == 4 and network.num_addresses > 2:
            return str(network.network_address + 1)
        if network.version == 6:
            return str(network.network_address + 1)
    return None


def has_cloudflare_link(html, cloudflare_asn="AS13335"):
    """Verify direct BGP adjacency from HE's IPv4/IPv6 peer tables."""
    soup = BeautifulSoup(html, "html.parser")
    target = cloudflare_asn.upper().replace(" ", "")
    for table in soup.find_all("table"):
        if "PEERS" not in table.get_text(" ", strip=True).upper():
            continue
        for row in table.find_all("tr"):
            row_text = row.get_text(" ", strip=True).upper().replace(" ", "")
            if re.search(rf"\b{re.escape(target)}\b", row_text):
                return True
    return False


def country_of_origin(html):
    """Extract HE's Country of Origin value for an ASN page."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    match = re.search(r"Country\s+of\s+Origin\s*:\s*([A-Za-z][A-Za-z .,'()&-]*?)(?=\s+(?:Internet Exchanges|Prefixes Originated|Prefixes Announced|RPKI|IPs Originated|AS Paths Observed|Average AS Path Length)\b|$)", text, re.I)
    return match.group(1).strip() if match else "UNKNOWN"
