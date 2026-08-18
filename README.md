# peerFinder

`peerFinder` collects prefixes from Cloudflare (`AS13335`) peers listed on BGP.HE. Its optional verification mode confirms each result against public RIPE RIS/RPKI data.

## Verification model

- **HE direct peer**: the ASN page on BGP.HE must list `AS13335` in its peer tables.
- **RIS observed neighbour**: RIPEstat is queried to see whether RIS collectors observe the ASN as a BGP neighbour of `AS13335`. A missing observation is not proof that a peer does not exist: collectors have incomplete Internet visibility.
- **RPKI**: a bounded sample of prefixes per peer receives a `valid`, `invalid_asn`, `invalid_length`, or `unknown` origin-validation status. RPKI validates the prefix origin ASN only; it does not validate the full AS path or commercial peering relationship.

The report is written to `output/verification.json`.

## Install

```bash
pip install -r requirements.txt
```

## Run

Fast collection uses six concurrent workers by default:

```bash
python main.py
```

Filter by country and write a BGP/RPKI report:

```bash
python main.py --country Germany,Netherlands --verify-bgp
```

Tune concurrency and RPKI sampling:

```bash
python main.py --workers 8 --verify-bgp --rpki-limit 10 --rpki-workers 8
```

- `--workers`: concurrent BGP.HE page fetches; default `6`.
- `--rpki-limit`: prefixes checked per accepted peer; default `10`. Set `0` to skip RPKI requests.
- `--rpki-workers`: concurrent RPKI API requests; default `8`.

HTTP responses are cached for 24 hours in `cache/`. A warm-cache run is substantially faster.

## Output

```text
output/
|-- Germany/
|   `-- EXAMPLE_AS64500.txt
`-- verification.json
```

Each peer file contains prefixes only. `verification.json` records the sources, generation time, RIS observation status, and sampled RPKI results.

