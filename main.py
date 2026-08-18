from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json
import os
import re

from bgp_verify import verification_report
from parser import country_of_origin, extract_peers, extract_subnets, has_cloudflare_link, split_subnets
from scraper import safe_get


URL = "https://bgp.he.net/AS13335#_peers"
OUT = "output"
CLOUDFLARE_ASN = "AS13335"


def clean(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_") or "UNKNOWN"


def parse_countries(value):
    if not value:
        return None
    return {item.strip().casefold() for item in value.split(",") if item.strip()}


def get_peer_data(peer):
    """Fetch and validate one HE peer page. Safe to call from a worker."""
    asn = peer["asn"]
    url = f"https://bgp.he.net/{asn}"
    html = safe_get(url).text
    if not has_cloudflare_link(html, CLOUDFLARE_ASN):
        return peer, None
    return peer, {"country": country_of_origin(html), "subnets": extract_subnets(html)}


def save_file(peer, subnets, country):
    folder = os.path.join(OUT, clean(country))
    os.makedirs(folder, exist_ok=True)
    filename = clean(peer["name"] + "_" + peer["asn"]) + ".txt"
    path = os.path.join(folder, filename)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(subnets) + "\n")
    return path


def save_verification_report(report):
    path = os.path.join(OUT, "verification.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Collect Cloudflare peer prefixes from HE, with optional RIS/RPKI verification."
    )
    parser.add_argument("--country", "-c", help="Comma-separated countries to save, e.g. Germany,Netherlands")
    parser.add_argument("--workers", type=int, default=6, help="Concurrent HE page fetches (default: 6)")
    parser.add_argument(
        "--verify-bgp",
        action="store_true",
        help="Write RIS-observed neighbour and RPKI prefix validation to output/verification.json",
    )
    parser.add_argument(
        "--rpki-limit",
        type=int,
        default=10,
        help="Prefixes to RPKI-check per accepted peer; 0 disables RPKI lookups (default: 10)",
    )
    parser.add_argument("--rpki-workers", type=int, default=8, help="Concurrent RPKI requests (default: 8)")
    args = parser.parse_args()

    if args.workers < 1 or args.rpki_workers < 1 or args.rpki_limit < 0:
        parser.error("--workers and --rpki-workers must be positive; --rpki-limit cannot be negative")

    allowed = parse_countries(args.country)
    print(f"Fetching Cloudflare peers ({CLOUDFLARE_ASN})...")
    peers = extract_peers(safe_get(URL).text)
    print(f"Peers found: {len(peers)} | HE workers: {args.workers}")
    if allowed:
        print("Country filter:", args.country)
    os.makedirs(OUT, exist_ok=True)

    accepted = []
    with ThreadPoolExecutor(max_workers=min(args.workers, len(peers) or 1)) as pool:
        futures = {pool.submit(get_peer_data, peer): peer for peer in peers}
        for future in as_completed(futures):
            peer = futures[future]
            try:
                peer, data = future.result()
            except Exception as exc:
                print("Error:", peer["asn"], exc)
                continue
            if data is None:
                print(f"Skipped {peer['asn']}: no observed HE peer link to {CLOUDFLARE_ASN}")
                continue
            if allowed and data["country"].casefold() not in allowed:
                print(f"Filtered {peer['asn']}: country={data['country']}")
                continue
            if not data["subnets"]:
                print("No prefixes:", peer["asn"])
                continue

            ipv4, ipv6 = split_subnets(data["subnets"])
            path = save_file(peer, data["subnets"], data["country"])
            accepted.append({**peer, **data})
            print(f"Saved: {path} | IPv4={len(ipv4)} | IPv6={len(ipv6)}")

    print(f"Accepted peers: {len(accepted)}")
    if args.verify_bgp:
        print("Checking RIS-observed neighbours and RPKI status...")
        try:
            report = verification_report(
                CLOUDFLARE_ASN,
                accepted,
                rpki_limit=args.rpki_limit,
                rpki_workers=args.rpki_workers,
            )
            path = save_verification_report(report)
            observed = sum(peer["ris_observed_neighbour"] for peer in report["peers"])
            print(f"Verification saved: {path} | RIS-observed peers: {observed}/{len(accepted)}")
        except Exception as exc:
            print("BGP verification unavailable:", exc)


if __name__ == "__main__":
    main()

