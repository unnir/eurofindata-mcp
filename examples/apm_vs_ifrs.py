"""Put issuer-defined APMs next to IFRS statement lines, over MCP (no SDK needed).

Usage:
    export EUROFINDATA_API_KEY=...                 # https://eurofindata.com/dashboard/api-keys
    python apm_vs_ifrs.py                          # LVMH (ISIN FR0000121014), FY2024
    python apm_vs_ifrs.py FR0000121014 2024-12-31

APMs (alternative performance measures) are not available on the REST API, so this
script speaks MCP Streamable HTTP directly with the standard library: initialize,
then two tools/call requests. Each APM keeps its original issuer label; it is not
relabelled as, or reconciled to, an IFRS line item.
"""
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MCP_URL = "https://api.eurofindata.com/mcp"
ticker = sys.argv[1] if len(sys.argv) > 1 else "FR0000121014"
period_end = sys.argv[2] if len(sys.argv) > 2 else "2024-12-31"

key = os.environ.get("EUROFINDATA_API_KEY")
if not key:
    raise SystemExit("Set EUROFINDATA_API_KEY first (free key: https://eurofindata.com/dashboard/api-keys).")

session = {}


def rpc(method, params=None, notify=False):
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if not notify:
        body["id"] = 1
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        **session,
    }
    try:
        with urlopen(Request(MCP_URL, json.dumps(body).encode(), headers), timeout=60) as response:
            if response.headers.get("Mcp-Session-Id"):
                session["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
            raw = response.read().decode()
    except HTTPError as error:
        raise SystemExit(f"{method}: HTTP {error.code} {error.reason}")
    except URLError as error:
        raise SystemExit(f"Network error: {error.reason}")
    if notify:
        return None
    if response.headers.get_content_type() == "text/event-stream":
        raw = next(line[5:] for line in raw.splitlines() if line.startswith("data:") and '"id"' in line)
    message = json.loads(raw)
    if "error" in message:
        raise SystemExit(f"{method}: {message['error']}")
    return message["result"]


def call(tool, **arguments):
    result = rpc("tools/call", {"name": tool, "arguments": arguments})
    data = result.get("structuredContent") or json.loads(result["content"][0]["text"])
    if isinstance(data, dict) and data.get("error"):
        raise SystemExit(f"{tool}: {data['error']}")
    return data


def bn(value):
    return "n/a" if value is None else f"{value / 1e9:,.3f}bn"


rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "eurofindata-mcp-example", "version": "0.1"}})
rpc("notifications/initialized", notify=True)

statements = call("get_income_statements", ticker=ticker, period="annual", limit=5)
row = next((r for r in statements.get("income_statements", []) if r.get("report_period") == period_end), None)
apms = call("get_apm_metrics", ticker=ticker, period_end=period_end, limit=20)

print(f"{statements.get('company', ticker)} - period ending {period_end}\n")
print("IFRS statement lines")
if row:
    for field in ("revenue", "operating_income", "net_income", "net_income_attributable"):
        print(f"  {field:<28} {row['currency']} {bn(row.get(field))}")
else:
    print("  no annual statement for this period (coverage gap, not a zero)")

print("\nIssuer-defined APMs (original labels; definitions live in the annual report)")
for a in apms.get("apm_metrics", []):
    print(f"  {a.get('label') or a.get('concept')}: {a.get('currency')} {bn(a.get('value'))}")
if not apms.get("apm_metrics"):
    print("  none extracted for this period (not evidence the issuer published none)")
