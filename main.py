from scraper import safe_get
from parser import extract_peers, extract_subnets, split_subnets, has_cloudflare_link, country_of_origin
import argparse
import os
import re

URL = "https://bgp.he.net/AS13335#_peers"
OUT = "output"
CLOUDFLARE_ASN = "AS13335"


def clean(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_") or "UNKNOWN"


def parse_countries(value):
    if not value:
        return None
    return {item.strip().casefold() for item in value.split(",") if item.strip()}


def get_peer_data(asn):
    url = f"https://bgp.he.net/{asn}"
    print("Checking peer graph/tables:", url)
    html = safe_get(url).text

    # HE's peer tables are the authoritative HTML representation of the
    # observed BGP adjacency. Do not accept an ASN merely because AS13335
    # appears elsewhere in the page.
    if not has_cloudflare_link(html, CLOUDFLARE_ASN):
        print(f"Skipped {asn}: no observed peer link to {CLOUDFLARE_ASN}")
        return None

    country = country_of_origin(html)
    subnets = extract_subnets(html)
    return country, subnets


def save_file(peer, subnets, country):
    folder = os.path.join(OUT, clean(country))
    os.makedirs(folder, exist_ok=True)
    filename = clean(peer["name"] + "_" + peer["asn"]) + ".txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as f:
        for subnet in subnets:
            f.write(subnet + "\n")
    print("Saved:", path, "subnets:", len(subnets))


def main():
    parser = argparse.ArgumentParser(
        description="Collect prefixes only from ASNs directly observed as Cloudflare peers on HE."
    )
    parser.add_argument(
        "--country", "-c",
        help="Only save peers from these countries, comma-separated. Examples: Germany or Germany,Netherlands"
    )
    args = parser.parse_args()
    allowed = parse_countries(args.country)

    print(f"Fetching Cloudflare peers ({CLOUDFLARE_ASN})...")
    html = safe_get(URL).text
    peers = extract_peers(html)
    print("Peers found:", len(peers))
    print("Adjacency filter: peer must list AS13335 in its HE peer tables")
    if allowed:
        print("Country filter:", args.country)
    os.makedirs(OUT, exist_ok=True)

    for peer in peers:
        try:
            data = get_peer_data(peer["asn"])
            if data is None:
                continue
            country, subnets = data
            if allowed and country.casefold() not in allowed:
                print(f"Filtered {peer['asn']}: country={country}")
                continue
            if not subnets:
                print("No prefixes:", peer["asn"])
                continue

            ipv4, ipv6 = split_subnets(subnets)
            print(f"Accepted {peer['asn']}: country={country} | IPv4={len(ipv4)} | IPv6={len(ipv6)}")
            save_file(peer, subnets, country)
        except Exception as exc:
            print("Error:", peer["asn"], exc)


if __name__ == "__main__":
    main()
