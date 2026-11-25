# European Financial Data — MCP server

**Give your AI agent European company financials straight from ESEF filings, with issuer-defined APMs and short-position disclosures, through one hosted MCP endpoint.**

```
https://api.eurofindata.com/mcp
```

- **Hosted, remote-only:** Streamable HTTP, nothing to install or run locally.
- **27 ESEF countries:** annual reports discovered daily from the EU's European Single Electronic Format filings. Every statement links back to its source filing.
- **More than statements:** issuer-defined alternative performance measures (APMs), net short positions from EU regulators, insider (PDMR) trades, major holdings, plus ISIN/LEI/MIC reference data.
- **Free testing:** 300 successful data requests per account per UTC day, shared across MCP and REST. You need an account, but no card. [Get a key →](https://eurofindata.com/dashboard/api-keys)

> Beta. Coverage depth and freshness vary by issuer and source. Call `get_company_coverage` and `get_data_freshness` before relying on a series. Docs: [eurofindata.com/docs](https://eurofindata.com/docs)

## Connect

Authentication is `Authorization: Bearer <account-api-key>`. Keep the key in an environment variable or in your client's secret config. Don't put it in a prompt, URL or repo.

### Claude Code

```bash
export EUROFINDATA_API_KEY=...   # from https://eurofindata.com/dashboard/api-keys
claude mcp add --transport http european-financial-data https://api.eurofindata.com/mcp \
  --header "Authorization: Bearer $EUROFINDATA_API_KEY"
```

Check it with `/mcp` or `claude mcp list`.

### Cursor

Merge into `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "european-financial-data": {
      "url": "https://api.eurofindata.com/mcp",
      "headers": { "Authorization": "Bearer <your-api-key>" }
    }
  }
}
```

### Codex

Merge into `~/.codex/config.toml`, with `EUROFINDATA_API_KEY` set in the environment Codex inherits:

```toml
[mcp_servers.european-financial-data]
url = "https://api.eurofindata.com/mcp"
bearer_token_env_var = "EUROFINDATA_API_KEY"
```

### Claude (web and desktop)

Add a custom connector with the URL `https://api.eurofindata.com/mcp` and sign in with OAuth. You don't need an API key for this.

**Verify:** ask your agent to *"call search_companies for ASML, then get_income_statements for ASML, annual, limit 1"*. You should get back a reporting period, currency and source.

## Tools

Below is a selection. Your client discovers the full list and its input schemas on connect, so let it rather than hard-coding arguments.

| Area | Tools | What you get |
| --- | --- | --- |
| Find a company | `search_companies`, `lookup_instrument`, `company_overview` | Resolve ticker, ISIN, LEI or name to one issuer |
| Coverage & freshness | `get_company_coverage`, `get_data_freshness` | Which datasets and periods exist, and when each source last refreshed |
| Statements | `get_income_statements`, `get_balance_sheets`, `get_cash_flow_statements`, `get_all_financials` | IFRS statements as filed in ESEF, annual / semi-annual / quarterly |
| Ratios & trends | `get_financial_metrics`, `company_trends`, `compare_companies`, `screen_companies` | Margins, returns, leverage, growth; peer comparisons and screens |
| Adjusted measures | `get_apm_metrics`, `get_operational_kpis`, `get_forward_guidance` | Issuer-defined APMs with original labels; sector KPIs; extracted guidance |
| Sources | `get_company_filings`, `get_sec_filings` | Filing URLs, periods, content hashes, superseded reports |
| Short selling | `get_short_positions`, `get_aggregate_short_interest` | Holder-level EU disclosures; UK aggregate totals (post-July 2026 regime) |
| Ownership & insiders | `get_insider_trades`, `get_major_holdings`, `get_beneficial_owners`, `get_corporate_ownership` | PDMR trades, threshold crossings, PSC and GLEIF ownership |
| Market & macro | `get_market_data`, `get_price_history`, `get_dividends`, `get_exchange_rate`, `convert_currency`, `get_bond_yields`, `get_macro` | Reference market data, ECB FX, yields, Eurostat/ECB macro |

Automatic share-price refresh is currently disabled, so treat price fields as historical rather than live quotes.

## Worked examples

### 1. LVMH: reported profit vs. issuer-defined APMs

**Prompt:**

> Find LVMH and check coverage for FY2024. Show its IFRS income-statement values and its alternative performance measures in two separate tables. Keep each APM's original label, and don't relabel recurring profit as net income.

**Tool calls:**

```text
search_companies(query="LVMH")
get_income_statements(ticker="FR0000121014", period="annual", limit=3)
get_apm_metrics(ticker="FR0000121014", period_end="2024-12-31")
```

**What comes back** (stored records, dated 4 Oct 2026 snapshot, EUR):

| Measure | Record type | EUR bn |
| --- | --- | ---: |
| Revenue | IFRS statement | 84.683 |
| Net profit, incl. non-controlling interests | IFRS statement | 12.958 |
| *Profit Loss From Operating Activities Recurring Including Share Of Profit Of Equity Accounted Investees* | Issuer APM | 19.571 |
| *Operating Free Cash Flow* | Issuer APM | 10.478 |
| *Cost Of Net Debt* | Issuer APM | 0.442 |

The €12.958bn is total net profit. The group share is €12.550bn, so the two can't be swapped when you calculate EPS. The recurring-profit APM includes associates, and that's part of its definition. Source: [LVMH 2024 ESEF filing](https://filings.xbrl.org/IOG4E947OATN0KJYSD45/2024-12-31/ESEF/FR/0/IOG4E947OATN0KJYSD45-2024-12-31-0-fr.json). Full walkthrough: [eurofindata.com/research/lvmh-reported-vs-adjusted-profit](https://eurofindata.com/research/lvmh-reported-vs-adjusted-profit). Script: [`examples/apm_vs_ifrs.py`](examples/apm_vs_ifrs.py).

### 2. ASML: five-year operating-margin history

**Prompt:**

> Compare ASML's operating margin across the last five annual periods. Show revenue, operating income, currency and the source filing for each year, and leave any missing values missing.

**Tool calls:**

```text
get_income_statements(ticker="ASML", period="annual", limit=5)
get_company_filings(ticker="ASML", limit=5)
```

**What comes back** (EU-IFRS/ESEF series, not ASML's US GAAP 20-F; 4 Oct 2026 snapshot):

| FY | Revenue (EUR bn) | Operating income (EUR bn) | Operating margin |
| --- | ---: | ---: | ---: |
| 2021 | 18.611 | 7.044 | 37.8% |
| 2022 | 21.173 | 7.321 | 34.6% |
| 2023 | 27.559 | 9.512 | 34.5% |
| 2024 | 28.263 | 9.937 | 35.2% |
| 2025 | 32.667 | 12.054 | 36.9% |

Each row links to its filing, e.g. [ASML 2025 ESEF](https://filings.xbrl.org/724500Y6DUVHQD6OXN27/2025-12-31/ESEF/NL/0/asml-2025-12-31-1-en.json). Script: [`examples/asml_margin_history.py`](examples/asml_margin_history.py). Article: [eurofindata.com/research/asml-operating-margin](https://eurofindata.com/research/asml-operating-margin).

### 3. European short-position disclosures

**Prompt:**

> Show the active disclosed net short positions in ASML. Name the regulator, position date and holder for each, keep holder-level records apart from any aggregate totals, and don't read an empty result as zero short interest.

**Tool calls:**

```text
get_company_coverage(ticker="ASML")
get_short_positions(ticker="ASML", active_only=true, limit=10)
get_aggregate_short_interest(ticker="<UK issuer>", current_only=true)   # UK publishes aggregates only since 13 Jul 2026
```

Holder-level disclosures come from AMF (FR), AFM (NL), BaFin (DE), CBI (IE), CNMV (ES), CONSOB (IT), FI (SE), Finanstilsynet, FMA (AT), FSMA (BE) and KNF (PL). Each record carries `holder_name`, `net_short_percent`, `position_date`, `publication_date`, `isin` and its `source`. Positions below national thresholds are never published, so a disclosure list is a lower bound on short exposure.

Script: [`examples/eu_short_radar.py`](examples/eu_short_radar.py) ranks the largest active disclosures across all regulators. Use `--source bafin` for one regulator or `--ticker` for one issuer. Method guide: [eurofindata.com/research/european-short-position-disclosures](https://eurofindata.com/research/european-short-position-disclosures).

## REST API

The same data is available over REST for scripts and notebooks: base URL `https://api.eurofindata.com/v1`, [OpenAPI](https://api.eurofindata.com/openapi.json), same bearer key, and the same daily allowance.

```bash
curl 'https://api.eurofindata.com/v1/financials/income-statements?ticker=ASML&period=annual&limit=5' \
  -H "Authorization: Bearer $EUROFINDATA_API_KEY"
```

APMs, KPIs, guidance and filings are MCP-only today. [`examples/apm_vs_ifrs.py`](examples/apm_vs_ifrs.py) shows how to call MCP from plain Python without an SDK.

## Examples

All scripts use only the Python standard library (3.9+) and read `EUROFINDATA_API_KEY` from the environment.

| Script | Interface | What it does |
| --- | --- | --- |
| [`eu_short_radar.py`](examples/eu_short_radar.py) | REST | Largest active net short disclosures, filterable by issuer or regulator |
| [`asml_margin_history.py`](examples/asml_margin_history.py) | REST | Multi-year revenue / operating income / margin for any covered issuer |
| [`apm_vs_ifrs.py`](examples/apm_vs_ifrs.py) | MCP over HTTP | IFRS lines next to issuer APMs for one period |

## Limits

- 300 successful data requests per account per UTC day across MCP, REST and the dashboard. Connecting and listing tools are free. On a `429`, honour `Retry-After`.
- Coverage is European listed issuers, and historical depth varies by issuer. Check `get_company_coverage` rather than assuming a 20-year history.
- KPI and guidance coverage is sparse, and guidance extraction is heuristic. Verify `raw_excerpt` against the source announcement.
- Hosted ChatGPT custom MCP connections are not verified yet. Claude (OAuth), Claude Code, Cursor and Codex are supported.

## MCP Registry

This repo holds the [`server.json`](server.json) for the official [MCP Registry](https://registry.modelcontextprotocol.io) entry `com.eurofindata/mcp`. [`.github/workflows/publish-mcp.yml`](.github/workflows/publish-mcp.yml) validates it on every push and publishes it on a `v*` tag.

## Links

[Website](https://eurofindata.com) · [Docs](https://eurofindata.com/docs) · [MCP setup](https://eurofindata.com/docs/mcp) · [Tools](https://eurofindata.com/docs/mcp-tools) · [Coverage](https://eurofindata.com/docs/coverage) · [Research](https://eurofindata.com/research) · [llms.txt](https://eurofindata.com/llms.txt) · [Contact](https://eurofindata.com/contact)

The example code in this repository is MIT-licensed. Data access is governed by the eurofindata.com terms.
