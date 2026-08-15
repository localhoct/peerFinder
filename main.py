from scraper import safe_get
from parser import extract_peers, extract_subnets, split_subnets, representative_ip, has_cloudflare_link
from geo import country_from_ip
import os
import re

URL = "https://bgp.he.net/AS13335#_peers"
OUT = "output"
CLOUDFLARE_ASN = "AS13335"


def clean(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_") or "UNKNOWN"


def get_peer_subnets(asn):
    url = f"https://bgp.he.net/{asn}"
    print("Checking graph:", url)
    html = safe_get(url).text

    # Only collect output when the peer graph contains a link/reference
    # to Cloudflare AS13335.
    if not has_cloudflare_link(html, CLOUDFLARE_ASN):
        print(f"Skipped {asn}: no graph link to {CLOUDFLARE_ASN}")
        return None

    print(f"Accepted {asn}: graph link to {CLOUDFLARE_ASN} found")
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
    print(f"Fetching Cloudflare peers ({CLOUDFLARE_ASN})...")
    html = safe_get(URL).text
    peers = extract_peers(html)
    print("Peers found:", len(peers))
    print(f"Graph filter: peer must link to {CLOUDFLARE_ASN}")
    os.makedirs(OUT, exist_ok=True)

    for peer in peers:
        try:
            subnets = get_peer_subnets(peer["asn"])
            if subnets is None:
                continue
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
