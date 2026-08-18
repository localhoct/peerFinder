"""BGP-adjacency and RPKI checks backed by RIPEstat/RIS data."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from scraper import safe_get


RIPESTAT_ROUTING_STATUS = "https://stat.ripe.net/data/routing-status/data.json"
RIPESTAT_RPKI = "https://stat.ripe.net/data/rpki-validation/data.json"
SOURCE_APP = "peerFinder"


def normalize_asn(value):
    """Return an ASN as ``AS<number>`` or None for invalid input."""
    text = str(value).strip().upper()
    if text.startswith("AS"):
        text = text[2:]
    if not text.isdigit():
        return None
    number = int(text)
    return f"AS{number}" if 0 < number <= 4294967295 else None


def _asns_in(value):
    """Extract ASN-shaped values from the variable observed_neighbours schema."""
    found = set()
    if isinstance(value, dict):
        for item in value.values():
            found.update(_asns_in(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            found.update(_asns_in(item))
    else:
        asn = normalize_asn(value)
        if asn:
            found.add(asn)
    return found


def observed_neighbours(asn):
    """Return ASNs that RIS currently observes as BGP neighbours of ``asn``."""
    response = safe_get(
        RIPESTAT_ROUTING_STATUS,
        params={"resource": normalize_asn(asn), "sourceapp": SOURCE_APP},
        delay=None,
    )
    data = response.json().get("data", {})
    return _asns_in(data.get("observed_neighbours", {}))


def validate_prefix(asn, prefix):
    """Return RIPEstat's RPKI state for one origin-ASN/prefix pair."""
    response = safe_get(
        RIPESTAT_RPKI,
        params={"resource": normalize_asn(asn), "prefix": prefix, "sourceapp": SOURCE_APP},
        delay=None,
    )
    data = response.json().get("data", {})
    return {
        "prefix": prefix,
        "status": data.get("status", "error"),
        "description": data.get("description", "No RPKI status returned"),
    }


def validate_prefixes(asn, prefixes, *, limit=10, workers=8):
    """Validate a bounded, deterministic sample of prefixes concurrently.

    ``limit=0`` deliberately disables RPKI requests. Limiting keeps a large
    peer list fast and avoids turning a discovery run into thousands of API calls.
    """
    selected = sorted(prefixes)[:limit] if limit else []
    results = []
    if not selected:
        return {"checked": 0, "states": {}, "prefixes": results}

    with ThreadPoolExecutor(max_workers=min(workers, len(selected))) as pool:
        futures = {pool.submit(validate_prefix, asn, prefix): prefix for prefix in selected}
        for future in as_completed(futures):
            prefix = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:  # Keep one failed public lookup from aborting the run.
                results.append({"prefix": prefix, "status": "error", "description": str(exc)})

    results.sort(key=lambda item: item["prefix"])
    states = Counter(item["status"] for item in results)
    return {"checked": len(results), "states": dict(sorted(states.items())), "prefixes": results}


def verification_report(cloudflare_asn, peer_rows, *, rpki_limit=10, rpki_workers=8):
    """Build a reproducible report for peers accepted by the HE adjacency check."""
    cloudflare_asn = normalize_asn(cloudflare_asn)
    observed = observed_neighbours(cloudflare_asn)
    ordered_peers = sorted(peer_rows, key=lambda item: item["asn"])
    rpki_results = {peer["asn"]: [] for peer in ordered_peers}
    check_plan = [
        (peer["asn"], normalize_asn(peer["asn"]), prefix)
        for peer in ordered_peers
        for prefix in sorted(peer["subnets"])[:rpki_limit]
    ] if rpki_limit else []

    # One global pool keeps the RPKI phase fast even when many peers are found.
    # The previous scraper was sequential; creating one pool per peer would only
    # move that bottleneck from HE to the validation API.
    if check_plan:
        with ThreadPoolExecutor(max_workers=min(rpki_workers, len(check_plan))) as pool:
            futures = {
                pool.submit(validate_prefix, asn, prefix): (peer_asn, prefix)
                for peer_asn, asn, prefix in check_plan
            }
            for future in as_completed(futures):
                peer_asn, prefix = futures[future]
                try:
                    rpki_results[peer_asn].append(future.result())
                except Exception as exc:
                    rpki_results[peer_asn].append(
                        {"prefix": prefix, "status": "error", "description": str(exc)}
                    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "bgp": "RIPEstat routing-status (RIS collector observations)",
            "rpki": "RIPEstat rpki-validation",
        },
        "cloudflare_asn": cloudflare_asn,
        "ris_observed_neighbour_count": len(observed),
        "peers": [],
    }

    for peer in ordered_peers:
        asn = normalize_asn(peer["asn"])
        prefix_results = sorted(rpki_results[peer["asn"]], key=lambda item: item["prefix"])
        rpki = {
            "checked": len(prefix_results),
            "states": dict(sorted(Counter(item["status"] for item in prefix_results).items())),
            "prefixes": prefix_results,
        }
        report["peers"].append(
            {
                "asn": asn,
                "name": peer["name"],
                "country": peer["country"],
                "he_direct_peer": True,
                "ris_observed_neighbour": asn in observed,
                "prefix_count": len(peer["subnets"]),
                "rpki": rpki,
            }
        )
    return report

