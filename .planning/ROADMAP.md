# Roadmap: TradingAgents — Vietnam Market & Enhanced Recommendations

**Created:** 2026-03-31
**Granularity:** Coarse (3-5 phases)
**Mode:** YOLO

## Milestone 1: Vietnam Market & Enhanced Recommendations

### Phase 1: Market Configuration & Detection

**Goal:** Establish multi-market foundation so the system can distinguish between VN and US tickers and route data requests to the correct vendor chain.

**Requirements:** MKTC-01, MKTC-02, MKTC-03, MKTC-04, MKTC-05

**Success Criteria:**
1. Config accepts `market` parameter ("US" | "VN") with env-based default
2. CLI prompts for market selection and passes it through the graph
3. Ticker market detection correctly classifies VN vs US tickers
4. AgentState includes market context, currency, and trading hours metadata
5. Existing US market functionality unchanged (backward compatible)

**UI hint**: no

---

### Phase 2: Vietnam Data Providers & Source Validation

**Goal:** Integrate vnstock and vietfin as Vietnamese data sources with cross-validation, and extend the vendor routing to handle VN-specific data fetching.

**Requirements:** VNDT-01, VNDT-02, VNDT-03, VNDT-04, VNDT-05, VNDT-06

**Success Criteria:**
1. `vnstock_provider.py` fetches OHLCV, fundamentals, listings for HOSE tickers
2. `vietfin_provider.py` acts as secondary source
3. `interface.py` routes VN tickers to VN vendors automatically
4. Cross-validation compares vnstock vs vietfin data and flags discrepancies
5. VNIndex composite data available via vnstock

**UI hint**: no

**Dependencies:** Phase 1 (market config must exist)

---

### Phase 3: Source Monitoring & User Notifications

**Goal:** Add transparent source tracking — users always know which data source is active for each category, get notified on failures, and see fallback chain in action.

**Requirements:** SRCM-01, SRCM-02, SRCM-03, SRCM-04, SRCM-05

**Success Criteria:**
1. Source status tracked per data category in agent state
2. User sees clear notification when a source fails
3. User sees fallback activation message naming both original and fallback source
4. Fallback chain VN: vnstock → vietfin → yfinance (with limitation warning) → error
5. CLI displays source status summary after each analysis run

**UI hint**: no

**Dependencies:** Phase 2 (VN data providers must exist to monitor)

---

### Phase 4: Enhanced Recommendations — Price Targets & Time Horizons

**Goal:** Upgrade recommendation output from simple BUY/SELL/HOLD to structured recommendations with long-term/short-term split, specific buy/sell price targets, and currency-aware output. Applies to all markets.

**Requirements:** EREC-01, EREC-02, EREC-03, EREC-04, EREC-05, EREC-06, EREC-07

**Success Criteria:**
1. Agent prompts request long-term AND short-term analysis separately
2. Output includes specific buy and sell price targets for each horizon
3. Price targets include currency code (VND or USD)
4. Sanity validation on price targets (within configurable % of current price)
5. Enhanced format works for both US and VN market analyses

**UI hint**: no

**Dependencies:** Phase 1 (market/currency context needed)

---

### Phase 5: Vietnamese News Integration

**Goal:** Enable the news analyst agent to fetch and analyze Vietnamese-language financial news, incorporating local news sentiment into the research debate for HOSE tickers.

**Requirements:** VNNW-01, VNNW-02, VNNW-03

**Success Criteria:**
1. Vietnamese news source returns relevant news for HOSE tickers
2. News analyst agent successfully processes Vietnamese-language content
3. Vietnamese news sentiment flows into bull/bear research debate
4. Graceful degradation — if news source fails, analysis continues without news (with warning)

**UI hint**: no

**Dependencies:** Phase 2 (VN data layer must exist)

---

## Summary

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Market Configuration & Detection | Multi-market foundation | MKTC-01–05 | 5 |
| 2 | Vietnam Data Providers & Source Validation | vnstock + vietfin integration | VNDT-01–06 | 5 |
| 3 | Source Monitoring & User Notifications | Transparent source tracking | SRCM-01–05 | 5 |
| 4 | Enhanced Recommendations | Price targets & time horizons | EREC-01–07 | 5 |
| 5 | Vietnamese News Integration | Local news sentiment | VNNW-01–03 | 4 |

**Total:** 5 phases | 26 requirements | 24 success criteria

## Dependency Graph

```
Phase 1 (Config) ──► Phase 2 (VN Data) ──► Phase 3 (Source Monitor)
     │                    │
     │                    └──► Phase 5 (VN News)
     │
     └──► Phase 4 (Enhanced Recs)
```

**Parallel opportunities:** Phase 4 can run in parallel with Phases 2-3 (only depends on Phase 1).

---

## Backlog

### Phase 999.1: Custom LLM Provider URL and Model Support (DONE)

**Goal:** Allow users to connect to any OpenAI-compatible API endpoint (e.g., cliproxyapi, LiteLLM proxy, vLLM, LocalAI) by specifying a custom base URL and arbitrary model name.

**Implementation:**
- `factory.py` — Routes `"custom"` provider to `OpenAIClient`
- `openai_client.py` — Handles custom base URL from config or `CUSTOM_LLM_BASE_URL` env var + `CUSTOM_API_KEY`
- `validators.py` — Exempts `"custom"` from model validation (any model accepted)
- `cli/utils.py` — Added "Custom (OpenAI-compatible)" option + prompts for URL, model name, API key
- `.env.example` — Added `CUSTOM_LLM_BASE_URL` and `CUSTOM_API_KEY` vars

**Verified:** All 4 integration tests pass (routing, validation, base_url wiring, error handling)

---
*Roadmap created: 2026-03-31*
*Last updated: 2026-04-01 after Phase 999.1 completed*
