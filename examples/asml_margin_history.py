"""Five-year operating-margin history from ESEF income statements (REST API).

Usage:
    export EUROFINDATA_API_KEY=...       # https://eurofindata.com/dashboard/api-keys
    python asml_margin_history.py        # ASML, last 5 annual periods
    python asml_margin_history.py SAP 10

Margin = operating income / revenue. A missing value stays missing; it is never
treated as zero. Amounts are full currency units. Stdlib only; one request.
"""
import json
import os
import sys
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ticker = sys.argv[1] if len(sys.argv) > 1 else "ASML"
periods = int(sys.argv[2]) if len(sys.argv) > 2 else 5

key = os.environ.get("EUROFINDATA_API_KEY")
if not key:
    raise SystemExit("Set EUROFINDATA_API_KEY first (free key: https://eurofindata.com/dashboard/api-keys).")

query = urlencode({"ticker": ticker, "period": "annual", "limit": periods})
request = Request(f"https://api.eurofindata.com/v1/financials/income-statements?{query}",
                  headers={"Authorization": f"Bearer {key}"})
try:
    with urlopen(request, timeout=30) as response:
        rows = json.load(response).get("income_statements", [])
except HTTPError as error:
    raise SystemExit(f"HTTP {error.code}: {error.reason}")
except URLError as error:
    raise SystemExit(f"Network error: {error.reason}")

if not rows:
    raise SystemExit(f"No annual statements for {ticker}. Check coverage; an empty result is not zero revenue.")


def billions(value):
    return "n/a" if value is None else f"{Decimal(value) / Decimal(10**9):,.2f}bn"


print(f"{ticker} annual income statements (ESEF / IFRS as filed)")
print(f"{'period':<12} {'ccy':<4} {'revenue':>12} {'op. income':>12} {'margin':>8}")
for r in sorted(rows, key=lambda r: r["report_period"]):
    revenue, op_income = r.get("revenue"), r.get("operating_income")
    margin = "n/a"
    if revenue and op_income is not None:
        margin = f"{Decimal(op_income) / Decimal(revenue) * 100:.1f}%"
    print(f"{r['report_period']:<12} {r['currency']:<4} {billions(revenue):>12} {billions(op_income):>12} {margin:>8}")
print("\nTrace any value to its filing with the MCP tool get_company_filings.")
