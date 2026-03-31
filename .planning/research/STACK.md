# Stack Research — Vietnamese Market Integration

## Recommended Stack Additions

### Primary: vnstock (Python library)
- **Package**: `vnstock` (latest — vnstock3 merged into main package)
- **Install**: `pip install -U vnstock`
- **Data source**: TCBS (Techcom Securities) public APIs
- **Capabilities**:
  - `stock_historical_data(symbol, start_date, end_date)` — OHLCV
  - `listing_companies()` — all HOSE/HNX/UPCOM tickers
  - `financial_report(symbol, report_type, frequency)` — BalanceSheet, IncomeStatement, CashFlow
  - Company profiles, stock screeners, real-time quotes
- **Auth**: Guest mode (limited) or free API key registration
- **Confidence**: ★★★★☆ High — most popular VN stock library, actively maintained
- **Risk**: Relies on TCBS public APIs which may change without notice

### Secondary: VietFin
- **Package**: `vietfin` (`pip install vietfin`)
- **Inspired by**: OpenBB framework
- **Value**: Unified interface across multiple Vietnamese brokerages
- **Confidence**: ★★★☆☆ Medium — newer, smaller community
- **Use case**: Cross-validation source (compare with vnstock data)

### Fallback: yfinance (existing)
- **VN support**: Limited — does NOT support `.VN` ticker suffix for individual HOSE stocks
- **Available**: VNM ETF (VanEck Vietnam ETF) for broad market exposure
- **Use case**: Fallback for market-level data or when VN-specific sources fail

### Vietnamese News Sources
- **cafef.vn**: Major Vietnamese financial news portal — scraping possible but fragile
- **vietstock.vn**: Financial data and news — offers DataFeed service
- **vnstock news features**: May include news data from TCBS
- **Approach**: Use LLM agents to process Vietnamese-language news (modern LLMs handle Vietnamese well)

### NOT Recommended for v1
- **SSI FastConnect API**: Requires active trading account, professional-grade — overkill for analysis-only
- **VNDirect API**: Account-based, not truly free/open
- **Direct web scraping** (cafef, vietstock): Fragile, ToS issues, maintenance burden

## Integration Pattern

Extend existing `interface.py` vendor routing:

```python
config["data_vendors"] = {
    "core_stock_apis": "vnstock",       # For VN market
    "technical_indicators": "vnstock",   # vnstock + stockstats
    "fundamental_data": "vnstock",       # Financial reports from TCBS
    "news_data": "vnstock",              # Vietnamese news
}
```

Market-aware routing: check ticker format → route to VN or US vendors.

## Versions (Verified 2026)

| Package | Version | Status |
|---------|---------|--------|
| vnstock | latest (unified from vnstock3) | Active, maintained |
| vietfin | latest | Active, smaller community |
| yfinance | >=0.2.63 | Already in project |

---
*Researched: 2026-03-31*
