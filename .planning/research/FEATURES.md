# Features Research — Vietnamese Market & Enhanced Recommendations

## Table Stakes (Must Have)

### Vietnam Market Data Access
- **OHLCV data for HOSE tickers** — historical and recent price data for Vietnamese stocks
- **Company listing** — enumerate all available HOSE tickers
- **Financial statements** — balance sheet, income statement, cash flow for VN companies
- **Market index data** — VNIndex composite data
- **Complexity**: Medium — vnstock provides most of this via TCBS

### Multi-Source Validation
- **Cross-source price comparison** — compare prices from vnstock vs vietfin vs yfinance
- **Data quality scoring** — flag discrepancies between sources
- **Complexity**: Medium — need alignment of data formats, timestamps, currency

### Source Transparency & Notifications
- **Active source display** — show which data source is being used for each data category
- **Failure notification** — alert user when a source fails and what fallback is active
- **Source health status** — summary of which sources are available
- **Complexity**: Low-Medium — mostly logging and UI feedback

### Enhanced Recommendations (All Markets)
- **Long-term vs short-term split** — separate analysis horizons
- **Buy price target** — specific price to enter position
- **Sell price target** — specific price to exit position
- **Confidence level** — how confident the system is in each target
- **Complexity**: Medium-High — requires prompt engineering for agents to output structured targets

### Market Configuration
- **Default market via environment** — `TRADINGAGENTS_DEFAULT_MARKET=VN`
- **Per-session market selection** — CLI option to choose market
- **Ticker format detection** — auto-detect VN vs US ticker format
- **Complexity**: Low — config extension

## Differentiators (Competitive Advantage)

### Vietnamese News Sentiment
- **Vietnamese-language news analysis** — pull and analyze local Vietnamese financial news
- **Cross-language comparison** — compare Vietnamese news sentiment with English coverage
- **Complexity**: Medium — LLMs handle Vietnamese but need specific news sources

### Fallback Chain with Tracking
- **Multi-tier fallback** — VN sources → yfinance → error with explanation
- **Fallback history** — log which sources were attempted and results
- **Complexity**: Low-Medium — extend existing fallback pattern

### Data Source Registry
- **Pluggable source registry** — easily add new Vietnamese or international data sources
- **Source health monitoring** — periodic check if sources are responsive
- **Complexity**: Medium — refactor of current vendor routing

## Anti-Features (Do NOT Build)

| Feature | Why Not |
|---------|---------|
| Real-time streaming | Batch analysis sufficient; streaming adds major complexity |
| Auto-trading execution | Legal/regulatory risk in VN market; recommendation-only safer |
| Paid data source integration | Barrier to adoption; free sources sufficient for v1 |
| HNX/UPCOM support | Focus on HOSE first; add later if needed |
| Mobile/web UI | CLI-first; existing pattern works |

## Feature Dependencies

```
Market Configuration ──► Vietnam Data Access ──► Multi-Source Validation
                                                        │
Vietnamese News ──────────────────────────────►  Enhanced Recommendations
                                                        │
Source Transparency ◄──────────────────────────── Fallback Chain
```

---
*Researched: 2026-03-31*
