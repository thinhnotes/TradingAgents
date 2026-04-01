# Phase 2 Research: Vietnam Data Providers & Source Validation

**Date:** 2026-03-31

## API Surface Summary

### vnstock (Primary VN Provider)
- **Package:** `pip install vnstock` (latest v3.4.0+, merged from vnstock3)
- **Auth:** Guest mode = 20 req/min (no key), Community = 60 req/min (free key)
- **Key modules:**
  - `stock.price.historical(symbol, start_date, end_date)` → OHLCV DataFrame
  - `stock.company.overview(symbol)` → Company profile
  - `stock.finance.income_statement(symbol, period, r_type)` → Income stmt
  - `stock.finance.balance_sheet(symbol, period, r_type)` → Balance sheet
  - `stock.finance.cash_flow(symbol, period, r_type)` → Cash flow
  - Market indices: `stock.price.historical(symbol='VNINDEX', ...)`
  - Listing: `Listing().all_symbols()` or similar
- **Returns:** Pandas DataFrames
- **Data source:** TCBS public API (unofficial wrapper)
- **Ticker format:** Uppercase, no suffix (e.g., 'FPT', 'VNM', 'VIC')

### vietfin (Secondary VN Provider)
- **Package:** `pip install vietfin` (v0.2.0, last released Apr 2024)
- **Import:** `from vietfin import vf`
- **Key methods:**
  - `vf.equity.search()` → List all stocks
  - `vf.equity.profile(symbol='vnm')` → Company profile
  - `vf.equity.historical(symbol='vnm')` → Historical prices
  - `vf.equity.fundamental.dividends(symbol)` → Dividends
  - `vf.equity.fundamental.ratios(symbol)` → Financial ratios
  - `vf.equity.fundamental.income(symbol)` → Income statement
  - `vf.equity.fundamental.management(symbol)` → Key executives
  - `vf.index.constituents(symbol='vn30')` → Index constituents
- **Returns:** DataFrames (OpenBB-inspired structure)
- **Deps:** httpx, pydantic, selectolax, pandas
- **⚠️ Low maturity:** 10 stars, 48 commits, last release Apr 2024

## Architecture Decisions

1. **File structure**: Follow alpha_vantage pattern — facade module + implementation files
   - `vnstock_provider.py` — facade re-exporting from impl files
   - `vnstock_ohlcv.py` — OHLCV + indicators
   - `vnstock_fundamentals.py` — financial statements
   - `vnstock_listings.py` — ticker listings + VNIndex
   - `vietfin_provider.py` — facade
   - `vietfin_ohlcv.py` — historical prices
   - `vietfin_fundamentals.py` — financial reports
   - `cross_validator.py` — source comparison logic

   **REVISED: Keep it simple.** Given the smaller API surface, use:
   - `vnstock_provider.py` — single file with all vnstock implementations
   - `vietfin_provider.py` — single file with all vietfin implementations
   - `cross_validator.py` — cross-validation logic

2. **Function signatures**: Must match existing yfinance/alpha_vantage patterns:
   - `get_stock_data(symbol, start_date, end_date)` → str
   - `get_fundamentals(ticker, curr_date=None)` → str
   - `get_balance_sheet(ticker, freq, curr_date=None)` → str
   - `get_cashflow(ticker, freq, curr_date=None)` → str
   - `get_income_statement(ticker, freq, curr_date=None)` → str
   - `get_insider_transactions(ticker)` → str (VN: stub/N/A)
   - `get_news(...)` → str (deferred to Phase 5)
   - `get_global_news(...)` → str (deferred to Phase 5)

3. **Cross-validation**: Triggered on demand, not on every call
   - Compare OHLCV data from vnstock vs vietfin for same ticker/date range
   - Configurable tolerance (e.g., 1% price difference)
   - Return validation report string

## Pitfalls to Address

1. **vnstock API instability**: Wrap imports in try/except, graceful error messages
2. **vietfin low maturity**: May break; treat as optional enhancement
3. **VN ticker format**: Always uppercase, no market suffix
4. **No insider transactions in VN**: Return clear "not available" message
5. **News deferred**: Phase 5 handles Vietnamese news; Phase 2 stubs return notice
