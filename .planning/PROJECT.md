# TradingAgents — Vietnam Market & Enhanced Recommendations

## What This Is

A multi-agent LLM framework for automated financial trading analysis that orchestrates specialized AI agents (analysts, researchers, debaters, portfolio managers) via LangGraph to produce trade recommendations. Currently supports US market data via yfinance and Alpha Vantage. Being extended to support the **Vietnamese stock market** (HOSE/VNIndex) with multiple free data sources, and enhanced to produce **price-targeted, time-horizon recommendations** across all markets.

## Core Value

Deliver actionable, multi-source-validated trade signals with specific buy/sell price targets and time horizons — starting with the Vietnamese market — while always being transparent about which data sources are active and any failures.

## Requirements

### Validated

<!-- Shipped and confirmed valuable — inferred from existing codebase. -->

- ✓ Multi-agent DAG orchestration via LangGraph (analysts → researchers → trader → risk debate → portfolio manager) — existing
- ✓ Tool-based data fetching (OHLCV, fundamentals, news, insider transactions) — existing
- ✓ Vendor-agnostic data routing with fallback (yfinance primary, Alpha Vantage alternative) — existing
- ✓ Multi-provider LLM support (OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama) — existing
- ✓ Two-tier LLM strategy (quick_thinking for analysts, deep_thinking for judges) — existing
- ✓ Bull vs Bear research debate with configurable rounds — existing
- ✓ Risk debate (aggressive / conservative / neutral) with Portfolio Manager judge — existing
- ✓ BM25-based agent memory with post-trade reflection — existing
- ✓ Interactive CLI with session management — existing
- ✓ Trade decision logging to JSON files — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Vietnam market integration — add HOSE/VNIndex support as a market option
- [ ] Configurable default market via environment (default: VN)
- [ ] Free Vietnamese data sources — research and integrate (VNDirect, vnstock, TCBS, SSI, cafef, etc.)
- [ ] Cross-validation between multiple Vietnamese data sources for accuracy
- [ ] Complementary data coverage — different sources for different data types (prices, news, fundamentals)
- [ ] Fallback chain — Vietnamese sources → Yahoo Finance, with user notification on failure
- [ ] Source transparency — always display which data source is currently active for each data type
- [ ] Source failure alerts — notify user when a source fails and which fallback is being used
- [ ] Vietnamese-language news analysis — pull and analyze Vietnamese news impacting HOSE stocks
- [ ] Enhanced recommendations — long-term and short-term recommendations with specific buy/sell price targets
- [ ] Price target output — each recommendation includes suggested buy price and sell price
- [ ] Time-horizon split — separate long-term vs short-term analysis and recommendations
- [ ] Apply enhanced recommendations to all markets (US and VN)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- HNX / UPCOM exchanges — focus on HOSE/VNIndex for v1, can add later
- Paid data source subscriptions — only integrating free data sources for now
- Broker execution integration — no auto-trading; recommendations only
- Real-time streaming data — batch analysis per request, not live feeds
- Mobile app — CLI-based for now

## Context

**Brownfield project:** Extending an existing v0.2.3 framework with a well-established architecture.

**Current architecture:**
- LangGraph StateGraph orchestrates analyst → debate → trade → risk layers
- `interface.py` already implements vendor routing with fallback pattern
- Data vendor abstraction (`VENDOR_METHODS` dict) is extensible — adding Vietnamese sources follows the same pattern
- Vietnamese market has specific nuances: VNDirect notation, HOSE ticker format, Vietnamese-language news sources

**Technical debt (from codebase map):**
- `validate_model()` not called in production graph
- Low test coverage across all components
- `cli/main.py` is a single 50KB file
- Global config state not thread-safe
- yfinance news scraping is fragile

**Vietnamese data source ecosystem:**
- `vnstock` — popular Python library for Vietnamese stock data
- VNDirect API — pricing and fundamentals
- TCBS — technical and fundamental data
- SSI (iBoard) — market data
- cafef.vn / vietstock.vn — news and analysis
- Need to research which are free, reliable, and have suitable APIs

## Constraints

- **Data sources**: Free APIs/libraries only — no paid subscriptions
- **Tech stack**: Must integrate into existing LangGraph/LangChain architecture
- **Vendor routing**: New sources must follow existing `interface.py` routing pattern
- **Backward compatibility**: US market support must continue working unchanged
- **Language**: Vietnamese news must be processable by the LLM agents (most modern LLMs handle Vietnamese)

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| HOSE/VNIndex only for v1 | Focus on the primary exchange first; most actively traded | — Pending |
| Free data sources only | Reduce barriers to adoption; can add premium later | — Pending |
| Market as configurable option (env-based default) | Users can set default market to VN; CLI auto-detects | — Pending |
| Enhanced recommendations for all markets | Price targets and time horizons benefit all users | — Pending |
| Vendor routing pattern reuse | Extend existing `interface.py` abstraction rather than building new | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-31 after initialization*
