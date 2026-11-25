"""List disclosed net short positions in European issuers (REST API).

Usage:
    export EUROFINDATA_API_KEY=...            # https://eurofindata.com/dashboard/api-keys
    python eu_short_radar.py                  # largest active disclosures, all regulators
    python eu_short_radar.py --ticker ASML    # one issuer (ticker, ISIN, LEI or name)
    python eu_short_radar.py --source bafin   # one regulator

These are holder-level regulatory disclosures above national thresholds. They are
not total short interest: positions below the threshold are not published, and an
empty result is not "zero shorts". UK aggregate data (post-July 2026 regime) is a
separate MCP tool, get_aggregate_short_interest. Stdlib only; one request.
"""
import argparse
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.eurofindata.com/v1"
SOURCES = ["amf", "afm", "bafin", "cbi", "cnmv", "consob", "fi", "finanstilsynet", "fma", "fsma", "knf"]

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--ticker", help="Issuer ticker, ISIN, LEI or name (optional)")
parser.add_argument("--source", choices=SOURCES, help="Regulator code (optional)")
parser.add_argument("--limit", type=int, default=25)
parser.add_argument("--include-closed", action="store_true", help="Include historical positions")
args = parser.parse_args()

key = os.environ.get("EUROFINDATA_API_KEY")
if not key:
    raise SystemExit("Set EUROFINDATA_API_KEY first (free key: https://eurofindata.com/dashboard/api-keys).")

params = {"limit": args.limit, "active_only": str(not args.include_closed).lower()}
if args.ticker:
    params["ticker"] = args.ticker
if args.source:
    params["source"] = args.source

request = Request(f"{API}/short-positions?{urlencode(params)}", headers={"Authorization": f"Bearer {key}"})
try:
    with urlopen(request, timeout=30) as response:
        rows = json.load(response).get("short_positions", [])
except HTTPError as error:
    hint = {401: "check the key", 404: "issuer not found", 429: "daily allowance used; see Retry-After"}
    raise SystemExit(f"HTTP {error.code}: {hint.get(error.code, error.reason)}")
except URLError as error:
    raise SystemExit(f"Network error: {error.reason}")

if not rows:
    raise SystemExit("No disclosed positions matched. That is a coverage/threshold result, not zero short interest.")

rows.sort(key=lambda r: r.get("net_short_percent") or 0, reverse=True)
print(f"{'net %':>6}  {'position date':<13} {'regulator':<14} {'issuer':<32} holder")
for r in rows:
    issuer = (r.get("issuer_name") or r.get("company_name") or r.get("isin") or "?")[:32]
    print(f"{r['net_short_percent']:>6.2f}  {r['position_date']:<13} {r['source']:<14} {issuer:<32} {r['holder_name']}")
print(f"\n{len(rows)} disclosures. Dates are position dates, not request time. Verify with the regulator's register.")
