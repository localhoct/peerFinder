from scraper import safe_get
from parser import extract_peers, extract_subnets, split_subnets, representative_ip
from geo import country_from_ip
import os
import re

URL = "https://bgp.he.net/AS13335#_peers"
OUT = "output"


def clean(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_") or "UNKNOWN"


def get_peer_subnets(asn):
    url = f"https://bgp.he.net/{asn}"
    print("Fetching:", url)
    html = safe_get(url).text
    return extract_subnets(html)


def save_file(peer, subnets, country):
    folder = os.path.join(OUT, country)
    os.makedirs(folder, exist_ok=True)
    filename = clean(peer["name"] + "_" + peer["asn"]) + ".txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        for subnet in subnets:
            f.write(subnet + "\n")
    print("Saved:", path, "subnets:", len(subnets))


def main():
    print("Fetching Cloudflare peers...")
    html = safe_get(URL).text
    peers = extract_peers(html)
    print("Peers found:", len(peers))
    os.makedirs(OUT, exist_ok=True)

    for peer in peers:
        try:
            subnets = get_peer_subnets(peer["asn"])
            if not subnets:
                print("No prefixes:", peer["asn"])
                continue

            ipv4, ipv6 = split_subnets(subnets)
            ip = representative_ip(subnets)
            country = country_from_ip(ip) if ip else "UNKNOWN"
            print(f"  IPv4: {len(ipv4)} | IPv6: {len(ipv6)} | Country: {country}")
            save_file(peer, subnets, country)
        except Exception as exc:
            print("Error:", peer["asn"], exc)


if __name__ == "__main__":
    main()
