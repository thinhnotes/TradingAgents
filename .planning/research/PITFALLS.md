# Pitfalls Research — Vietnamese Market Integration

## 1. vnstock API Instability
- **Risk**: vnstock wraps TCBS public APIs that are undocumented and can change without notice
- **Warning signs**: Method calls returning empty DataFrames, HTTP 403/429 errors
- **Prevention**: Implement robust error handling, cache responses, validate data shape after every call
- **Phase**: Phase 2 (VN Data Providers)

## 2. Ticker Format Confusion
- **Risk**: Vietnamese tickers (e.g., `FPT`, `VNM`, `VIC`) may collide with US ticker symbols
- **Warning signs**: Wrong market data returned for ambiguous tickers
- **Prevention**: Explicit market context in all data calls; never guess market from ticker alone; use `.VN` suffix convention or explicit market parameter
- **Phase**: Phase 1 (Config & Market Detection)

## 3. Vietnamese News Source Fragility
- **Risk**: Vietnamese financial news sites (cafef, vietstock) are scraping-hostile — frequent layout changes, anti-bot measures
- **Warning signs**: Empty news results, HTML errors, IP blocking
- **Prevention**: Use vnstock's built-in news features first; avoid custom scraping; implement graceful degradation (no news ≠ system failure)
- **Phase**: Phase 5 (Vietnamese News)

## 4. Currency and Price Format
- **Risk**: Vietnamese stocks priced in VND (thousands — e.g., 85,000 VND). US stocks in USD. Agents may confuse prices
- **Warning signs**: LLM recommending "buy at 85" (missing thousands), or comparing VND and USD prices
- **Prevention**: Always include currency in agent context; normalize output to include currency code; validate price range sanity
- **Phase**: Phase 1 (Config), Phase 4 (Enhanced Recommendations)

## 5. T+2 Settlement & Trading Hours
- **Risk**: Vietnamese market has different trading hours (9:00-15:00 ICT) and T+2 settlement. ATC session at 14:30-15:00
- **Warning signs**: Agents analyzing "current" data outside market hours; settlement delays not reflected
- **Prevention**: Include market hours context in agent prompts; note that data may be delayed; handle timezone properly
- **Phase**: Phase 1 (Config)

## 6. yfinance VN Fallback Limitations  
- **Risk**: yfinance does NOT support `.VN` suffix for individual HOSE tickers — fallback is very limited
- **Warning signs**: Empty data when falling back to yfinance for VN tickers
- **Prevention**: Be transparent that yfinance fallback provides market-level data only (VNM ETF); not individual VN stocks. Clearly communicate this limitation to users
- **Phase**: Phase 3 (Source Monitoring)

## 7. Enhanced Recommendations Hallucination
- **Risk**: LLMs may hallucinate specific price targets without proper data grounding
- **Warning signs**: Price targets far from current price, inconsistent targets between agents
- **Prevention**: Provide current price + technical levels in agent context; add sanity checks on output targets (within reasonable % of current price); require agents to cite data sources for targets
- **Phase**: Phase 4 (Enhanced Recommendations)

## 8. Cross-Validation False Alarms
- **Risk**: Different data sources may have legitimate timing differences (not actual discrepancies)
- **Warning signs**: Constant validation warnings that are actually just timing delays
- **Prevention**: Allow configurable tolerance for cross-validation (e.g., price within 1%); timestamp-aware comparison; don't compare real-time vs delayed data
- **Phase**: Phase 2 (VN Data Providers)

## 9. vnstock Rate Limiting / Authentication
- **Risk**: vnstock may require API key registration for full access (guest mode has limits)
- **Warning signs**: Data requests returning partial results or error messages about authentication
- **Prevention**: Document API key setup clearly; handle guest mode gracefully; implement request throttling
- **Phase**: Phase 2 (VN Data Providers)

## 10. Existing Test Debt
- **Risk**: Adding Vietnamese market support without tests compounds existing low test coverage
- **Warning signs**: Regressions in US market functionality when VN code is added
- **Prevention**: Write tests for new VN provider code; at minimum test vendor routing, market detection, and data format validation
- **Phase**: All phases

---
*Researched: 2026-03-31*
