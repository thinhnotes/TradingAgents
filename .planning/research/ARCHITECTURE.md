# Architecture Research — Vietnamese Market Integration

## Component Architecture

### Market-Aware Vendor Routing (Extension of interface.py)

```
User Input (ticker, market?)
        │
        ▼
  Market Detector
  ├── Is VN ticker? → VN vendor chain
  ├── Is US ticker? → US vendor chain (existing)
  └── Unknown? → prompt user
        │
        ▼
  VN Vendor Chain
  ├── vnstock (primary) ──► TCBS data
  ├── vietfin (secondary) ──► cross-validation
  └── yfinance (fallback) ──► limited VN data
        │
        ▼
  Source Status Reporter
  ├── Log active source per data category
  ├── Notify on failure/fallback
  └── Track source health
```

### Integration Points with Existing Architecture

1. **Config Layer** (`default_config.py`)
   - Add `market` field (default: "VN" via env)
   - Add VN-specific vendor routing config
   - Add `recommendation_mode` for price targets

2. **Dataflows Layer** (`tradingagents/dataflows/`)
   - New: `vnstock_provider.py` — wraps vnstock library
   - New: `vietfin_provider.py` — wraps vietfin library
   - New: `source_monitor.py` — tracks source health, notifications
   - Modified: `interface.py` — market-aware routing logic
   - Modified: `VENDOR_METHODS` dict — add VN vendor entries

3. **Agent Layer** (`tradingagents/agents/`)
   - Modified: Agent prompts to support Vietnamese context/news
   - Modified: Tool functions to accept market parameter
   - New: Vietnamese news tools

4. **Graph Layer** (`tradingagents/graph/`)
   - Modified: `trading_graph.py` — pass market context through state
   - Modified: `AgentState` — add `market`, `source_status`, `price_targets`
   - Modified: Signal processing — enhanced output with price targets

5. **CLI Layer** (`cli/main.py`)
   - Modified: Add market selection option
   - Modified: Display source status in output
   - Modified: Show enhanced recommendations format

### Data Flow for VN Market

```
AgentState["market"] = "VN"
        │
        ▼
  Market Analyst ──► vnstock.stock_historical_data()
  News Analyst ──► Vietnamese news sources
  Fundamental Analyst ──► vnstock.financial_report()
  Social Analyst ──► Vietnamese social sources
        │
        ▼
  Bull/Bear Debate (VN-contextualized prompts)
        │
        ▼
  Trader ──► Enhanced recommendation prompt
        │   (includes buy/sell price targets, short/long term)
        ▼
  Risk Debate ──► Enhanced output format
        │
        ▼
  Final Output:
  {
    "decision": "BUY",
    "short_term": { "target_buy": 85000, "target_sell": 92000, "horizon": "1-3 months" },
    "long_term": { "target_buy": 80000, "target_sell": 110000, "horizon": "6-12 months" },
    "active_sources": { "prices": "vnstock", "news": "cafef", "fundamentals": "vnstock" },
    "source_warnings": ["vietfin unavailable — using vnstock only"]
  }
```

### Suggested Build Order

1. **Config & Market Detection** — foundation for everything else
2. **VN Data Providers** — vnstock + vietfin integration
3. **Source Monitoring & Notifications** — transparency layer
4. **Enhanced Recommendations** — agent prompt engineering + output parsing
5. **Vietnamese News** — news source integration

---
*Researched: 2026-03-31*
