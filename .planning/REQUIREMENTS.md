# Requirements: TradingAgents — Vietnam Market & Enhanced Recommendations

**Defined:** 2026-03-31
**Core Value:** Deliver actionable, multi-source-validated trade signals with specific buy/sell price targets and time horizons — starting with the Vietnamese market — while always being transparent about which data sources are active and any failures.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Market Configuration

- [ ] **MKTC-01**: System supports multiple markets (US, VN) via config parameter
- [ ] **MKTC-02**: Default market configurable via environment variable (`TRADINGAGENTS_DEFAULT_MARKET`)
- [ ] **MKTC-03**: CLI allows user to select market (US or VN) per session
- [ ] **MKTC-04**: System auto-detects ticker market context to route to correct data vendors
- [ ] **MKTC-05**: Market-specific metadata (currency, trading hours, exchange name) available in agent state

### Vietnam Data Providers

- [ ] **VNDT-01**: System can fetch OHLCV data for HOSE tickers via vnstock
- [ ] **VNDT-02**: System can fetch financial statements (balance sheet, income statement, cash flow) for HOSE tickers via vnstock
- [ ] **VNDT-03**: System can list all available HOSE tickers via vnstock
- [ ] **VNDT-04**: System can fetch VNIndex composite data
- [ ] **VNDT-05**: System integrates vietfin as secondary data source for cross-validation
- [ ] **VNDT-06**: Cross-validation compares prices from vnstock vs vietfin and flags discrepancies beyond configurable tolerance

### Source Monitoring & Notifications

- [ ] **SRCM-01**: System displays which data source is active for each data category (prices, fundamentals, news)
- [ ] **SRCM-02**: System notifies user when a data source fails with clear error message
- [ ] **SRCM-03**: System notifies user when falling back to alternative source (and names both sources)
- [ ] **SRCM-04**: Fallback chain for VN: vnstock → vietfin → yfinance (with limitation warning) → error
- [ ] **SRCM-05**: Source status summary displayed in CLI output after each analysis run

### Enhanced Recommendations

- [ ] **EREC-01**: System produces separate long-term and short-term recommendations
- [ ] **EREC-02**: Each recommendation includes specific buy price target
- [ ] **EREC-03**: Each recommendation includes specific sell price target
- [ ] **EREC-04**: Each recommendation includes time horizon (e.g., "1-3 months", "6-12 months")
- [ ] **EREC-05**: Enhanced recommendation format applies to all markets (US and VN)
- [ ] **EREC-06**: Price targets include currency code (VND for VN, USD for US)
- [ ] **EREC-07**: Price targets validated against current price for sanity (within reasonable range)

### Vietnamese News

- [ ] **VNNW-01**: System can fetch Vietnamese-language financial news relevant to HOSE tickers
- [ ] **VNNW-02**: News analyst agent can process and analyze Vietnamese-language news
- [ ] **VNNW-03**: Vietnamese news sentiment incorporated into bull/bear research debate

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Market Coverage

- **EXTM-01**: Support HNX exchange tickers
- **EXTM-02**: Support UPCOM exchange tickers
- **EXTM-03**: Support additional Asian markets (Thailand, Indonesia)

### Advanced Source Management

- **ASRC-01**: Source health monitoring dashboard (periodic background checks)
- **ASRC-02**: Pluggable data source registry (add new sources without code changes)
- **ASRC-03**: Historical source reliability scoring

### Premium Data Integration

- **PRDT-01**: SSI FastConnect API integration (requires trading account)
- **PRDT-02**: VNDirect API integration (requires account)
- **PRDT-03**: Vietstock DataFeed integration (paid)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time streaming data | Batch analysis sufficient; streaming adds major complexity |
| Auto-trading execution | Legal/regulatory risk in VN market; recommendations only |
| Paid data source subscriptions | Barrier to adoption; only free sources for v1 |
| HNX/UPCOM exchanges | Focus on HOSE first; tracked as v2 |
| Mobile/web UI | CLI-first; existing pattern works |
| Direct web scraping (cafef, vietstock) | Fragile, ToS issues; use library wrappers instead |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MKTC-01 | Phase 1 | Pending |
| MKTC-02 | Phase 1 | Pending |
| MKTC-03 | Phase 1 | Pending |
| MKTC-04 | Phase 1 | Pending |
| MKTC-05 | Phase 1 | Pending |
| VNDT-01 | Phase 2 | Pending |
| VNDT-02 | Phase 2 | Pending |
| VNDT-03 | Phase 2 | Pending |
| VNDT-04 | Phase 2 | Pending |
| VNDT-05 | Phase 2 | Pending |
| VNDT-06 | Phase 2 | Pending |
| SRCM-01 | Phase 3 | Pending |
| SRCM-02 | Phase 3 | Pending |
| SRCM-03 | Phase 3 | Pending |
| SRCM-04 | Phase 3 | Pending |
| SRCM-05 | Phase 3 | Pending |
| EREC-01 | Phase 4 | Pending |
| EREC-02 | Phase 4 | Pending |
| EREC-03 | Phase 4 | Pending |
| EREC-04 | Phase 4 | Pending |
| EREC-05 | Phase 4 | Pending |
| EREC-06 | Phase 4 | Pending |
| EREC-07 | Phase 4 | Pending |
| VNNW-01 | Phase 5 | Pending |
| VNNW-02 | Phase 5 | Pending |
| VNNW-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 after initial definition*
