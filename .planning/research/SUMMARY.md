# Research Summary — Vietnamese Market & Enhanced Recommendations

## Key Findings

### Stack
- **vnstock** is the clear primary choice — most popular VN stock Python library, wraps TCBS data, provides OHLCV + fundamentals + company listings
- **vietfin** as secondary source for cross-validation (OpenBB-inspired, multi-brokerage)
- **yfinance has NO individual VN stock support** — only VNM ETF for broad market exposure; fallback is limited
- SSI FastConnect and VNDirect APIs require trading accounts — excluded from v1

### Table Stakes Features
- HOSE/VNIndex data access via vnstock (price, fundamentals, listings)
- Multi-source validation (vnstock vs vietfin)
- Source transparency and failure notifications
- Market configuration (default: VN, configurable via env)
- Enhanced recommendations with price targets and time horizons (all markets)

### Architecture
- Extends existing `interface.py` vendor routing pattern — no major refactor needed
- Market detector determines VN vs US → routes to appropriate vendor chain
- State extended with `market`, `source_status`, `price_targets` fields
- Build order: Config → VN Data → Source Monitoring → Enhanced Recs → VN News

### Critical Watch Items
1. **vnstock API instability** — undocumented TCBS APIs can change; need robust error handling
2. **Ticker collision** — VN and US tickers overlap (e.g., `VNM`); must always use explicit market context
3. **yfinance fallback is weak for VN** — can only provide ETF-level data, not individual stocks
4. **VND pricing** — thousands-scale (85,000 VND vs $85 USD); agents must handle currency correctly
5. **Price target hallucination** — LLMs need current price + technical data to ground recommendations

### Recommended Approach

| Phase | Focus | Dependencies |
|-------|-------|-------------|
| 1 | Config & Market Detection | Foundation — no dependencies |
| 2 | VN Data Providers (vnstock + vietfin) | Phase 1 |
| 3 | Source Monitoring & Notifications | Phase 2 |
| 4 | Enhanced Recommendations (all markets) | Phase 1 |
| 5 | Vietnamese News Integration | Phase 2 |

### Risk Assessment
- **Technical risk**: Medium — vnstock is community-maintained, may break
- **Integration risk**: Low — follows existing architecture patterns
- **Scope risk**: Low — well-bounded features with clear boundaries

---
*Synthesized: 2026-03-31*
