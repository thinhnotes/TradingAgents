# Phase 1: Market Configuration & Detection — Research

## Objective

Research how to implement multi-market configuration (US/VN) into the existing TradingAgents framework so the system can distinguish between VN and US tickers and route data requests correctly.

## Current Architecture Analysis

### Config System (`tradingagents/default_config.py`)
- Dictionary-based config with `data_vendors` and `tool_vendors` keys
- No `market` field exists — needs to be added
- Config is global via `tradingagents/dataflows/config.py` (module-level `_config` dict)
- `set_config()` called once in `TradingAgentsGraph.__init__()` — good injection point

### Vendor Routing (`tradingagents/dataflows/interface.py`)
- `route_to_vendor(method, *args, **kwargs)` dispatches to implementations
- `VENDOR_METHODS` dict maps method names → vendor → implementation function
- `VENDOR_LIST` only contains `["yfinance", "alpha_vantage"]` — needs VN vendors
- Fallback: primary vendors → remaining available; currently only catches `AlphaVantageRateLimitError`

### Agent State (`tradingagents/agents/utils/agent_states.py`)
- `AgentState(MessagesState)` has `company_of_interest` and `trade_date`
- No market, currency, or market metadata fields
- Adding fields to TypedDict is backward-compatible (existing code ignores them)

### Propagation (`tradingagents/graph/propagation.py`)
- `create_initial_state(company_name, trade_date)` — no market parameter
- `company_of_interest` is just the ticker string (e.g., "AAPL")
- Initial state needs market context

### CLI Entry Point (`cli/main.py`)
- Large monolithic file — user selects ticker interactively or via arg
- No market selection exists — needs prompt or param

## Design Decisions

### 1. Market Representation
- **Key**: `market` field in config, values: `"US"` | `"VN"`
- **Environment**: `TRADINGAGENTS_DEFAULT_MARKET` env var, default `"US"` for backward compat
- **Override**: `TradingAgentsGraph(config={"market": "VN"})` or CLI flag

### 2. Ticker Market Detection Logic
Vietnamese tickers: 3-letter uppercase (e.g., `FPT`, `VNM`, `VIC`, `HPG`, `SSI`, `TCB`)
US tickers: 1-5 letter uppercase (e.g., `AAPL`, `MSFT`, `TSLA`, `A`)

**Problem**: `VNM` is both a Vietnamese ticker and a US ETF ticker. Pure regex won't work.
**Solution**: Explicit market context always takes precedence. Detection is advisory only.

```python
# Market detection heuristic (advisory, not authoritative)
KNOWN_VN_EXCHANGES = {"HOSE", "HNX", "UPCOM"}

def detect_market(ticker: str, explicit_market: str = None) -> str:
    """Detect market for a ticker. Explicit market takes precedence."""
    if explicit_market:
        return explicit_market
    # Check against known VN ticker lists if available
    # Otherwise use configured default
    return get_config().get("market", "US")
```

### 3. Market Metadata
Each market has different properties:

```python
MARKET_METADATA = {
    "US": {
        "currency": "USD",
        "exchange": "NYSE/NASDAQ",
        "trading_hours": "09:30-16:00 ET",
        "settlement": "T+1",
        "price_unit": 1,  # prices are in dollars
    },
    "VN": {
        "currency": "VND",
        "exchange": "HOSE",
        "trading_hours": "09:00-15:00 ICT",
        "settlement": "T+2",
        "price_unit": 1000,  # prices often in thousands
    }
}
```

### 4. Config Changes
Add to `DEFAULT_CONFIG`:
```python
"market": os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US"),
```

### 5. AgentState Changes
Add to `AgentState`:
```python
market: Annotated[str, "Market context (US or VN)"]
market_metadata: Annotated[dict, "Market metadata (currency, exchange, trading hours)"]
```

### 6. Vendor Routing Changes
`interface.py` needs market-aware routing:
- If `market == "VN"`: route to VN vendors (vnstock, vietfin) — Phase 2 adds these
- If `market == "US"`: route to current vendors (yfinance, alpha_vantage)
- For Phase 1: just the config and routing infrastructure. Actual VN vendor implementations come in Phase 2.

### 7. Backward Compatibility
- `market` defaults to `"US"` → all existing behavior unchanged
- New fields in `AgentState` are optional (TypedDict doesn't enforce)
- `propagate(company_name, trade_date)` signature unchanged — market comes from config
- Existing tool functions just get passed through to existing vendors

## Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `tradingagents/default_config.py` | Modify | Add `market` field |
| `tradingagents/dataflows/interface.py` | Modify | Add market-aware routing |
| `tradingagents/agents/utils/agent_states.py` | Modify | Add market fields to AgentState |
| `tradingagents/graph/propagation.py` | Modify | Include market context in initial state |
| `tradingagents/graph/trading_graph.py` | Modify | Pass market context |
| `tradingagents/dataflows/market_config.py` | New | Market metadata and detection |

## Risks

1. **Ticker collision** (VNM exists in both markets) — mitigated by explicit market context
2. **Global config state** — existing issue, not introduced by this change
3. **CLI changes** — cli/main.py is large, minimize changes to just market selection

## RESEARCH COMPLETE

---
*Phase: 01-market-configuration-detection*
*Researched: 2026-03-31*
