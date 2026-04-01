# Phase 2: Vietnam Data Providers & Source Validation — PLAN

**Phase:** 02
**Status:** Planning
**Requirements:** VNDT-01, VNDT-02, VNDT-03, VNDT-04, VNDT-05, VNDT-06

---

## Plan 1: vnstock Provider Implementation

### Goal
Create `vnstock_provider.py` that implements all data-fetching functions for HOSE tickers using the `vnstock` library, matching existing function signatures from `y_finance.py`.

### Files
- **[NEW]** `tradingagents/dataflows/vnstock_provider.py`

### Implementation Details

Implement these functions with signatures matching existing yfinance pattern:

1. **`get_stock_data(symbol, start_date, end_date)`** → str
   - Uses `vnstock` `Vnstock().stock(symbol).quote.history(start, end)`
   - Returns formatted CSV string with header

2. **`get_fundamentals(ticker, curr_date=None)`** → str
   - Fetches company overview/profile
   - Returns formatted key-value string

3. **`get_balance_sheet(ticker, freq='quarterly', curr_date=None)`** → str
   - Fetches balance sheet from vnstock finance module
   - Returns CSV string

4. **`get_cashflow(ticker, freq='quarterly', curr_date=None)`** → str
   - Fetches cash flow statement
   - Returns CSV string

5. **`get_income_statement(ticker, freq='quarterly', curr_date=None)`** → str
   - Fetches income statement
   - Returns CSV string

6. **`get_insider_transactions(ticker)`** → str
   - Returns "Insider transaction data is not available for Vietnamese stocks"

7. **`get_news(symbol, ...)`** → str
   - Stub: Returns "Vietnamese news integration planned for Phase 5"

8. **`get_global_news()`** → str
   - Stub: Returns "Vietnamese global news integration planned for Phase 5"

9. **`get_vnindex_data(start_date, end_date)`** → str
   - Fetches VNIndex composite data using vnstock
   - Returns formatted CSV

10. **`get_available_tickers()`** → list
    - Returns list of available HOSE tickers via vnstock Listing

### Error Handling
- All functions wrapped in try/except
- Import vnstock lazily (at function call time) to avoid import errors if not installed
- Clear error messages including "pip install vnstock" hint

### UAT
- [ ] `get_stock_data('FPT', '2025-01-01', '2025-03-31')` returns valid OHLCV CSV
- [ ] `get_fundamentals('FPT')` returns company profile string
- [ ] `get_balance_sheet('FPT')` returns balance sheet CSV
- [ ] `get_vnindex_data('2025-01-01', '2025-03-31')` returns index data
- [ ] `get_available_tickers()` returns list of HOSE tickers
- [ ] Error when vnstock not installed gives clear message

---

## Plan 2: vietfin Provider Implementation

### Goal
Create `vietfin_provider.py` that implements data-fetching functions using the `vietfin` library as a secondary cross-validation source.

### Files
- **[NEW]** `tradingagents/dataflows/vietfin_provider.py`

### Implementation Details

Same function signatures as vnstock_provider:

1. **`get_stock_data(symbol, start_date, end_date)`** → str
   - Uses `vf.equity.historical(symbol=symbol, start=start_date, end=end_date)`
   - Returns formatted CSV string

2. **`get_fundamentals(ticker, curr_date=None)`** → str
   - Uses `vf.equity.profile(symbol=ticker)` + `vf.equity.fundamental.ratios(symbol=ticker)`
   - Returns formatted key-value string

3. **`get_income_statement(ticker, freq='quarterly', curr_date=None)`** → str
   - Uses `vf.equity.fundamental.income(symbol=ticker)`
   - Returns CSV string

4. **`get_balance_sheet(ticker, freq='quarterly', curr_date=None)`** → str
   - Stub (vietfin may not have this): Returns "Balance sheet not available via vietfin"

5. **`get_cashflow(ticker, freq='quarterly', curr_date=None)`** → str
   - Stub: Returns "Cash flow not available via vietfin"

6. **`get_insider_transactions(ticker)`** → str
   - Returns "Not available for Vietnamese stocks via vietfin"

### Error Handling
- Same lazy-import pattern as vnstock_provider
- "pip install vietfin" hint on ImportError
- Graceful handling of API failures

### UAT
- [ ] `get_stock_data('VNM', '2025-01-01', '2025-03-31')` returns valid data
- [ ] `get_fundamentals('VNM')` returns company info
- [ ] ImportError handled gracefully when vietfin not installed

---

## Plan 3: Cross-Validation Module

### Goal
Create `cross_validator.py` that compares data from vnstock vs vietfin for the same ticker and flags discrepancies that exceed a configurable tolerance.

### Files
- **[NEW]** `tradingagents/dataflows/cross_validator.py`

### Implementation Details

1. **`validate_ohlcv(symbol, start_date, end_date, tolerance=0.01)`** → str
   - Fetches OHLCV from both vnstock and vietfin
   - Compares Close prices for matching dates
   - Flags dates where price difference > tolerance (default 1%)
   - Returns validation report string

2. **`validate_fundamentals(symbol, tolerance=0.05)`** → str
   - Compares key metrics from both sources
   - Reports which fields match/differ
   - Returns validation report

3. **`run_full_validation(symbol, start_date, end_date)`** → str
   - Runs both OHLCV and fundamentals validation
   - Returns comprehensive report

### Config
- Add `cross_validation_tolerance` to DEFAULT_CONFIG (default: 0.01 = 1%)

### UAT
- [ ] Validation report correctly identifies matching data
- [ ] Validation report flags genuine discrepancies
- [ ] Graceful handling when one source fails (reports partial result)

---

## Plan 4: Interface Registration & Routing

### Goal
Register vnstock and vietfin implementations in `interface.py` VENDOR_METHODS so the routing system can dispatch to them for VN market tickers.

### Files
- **[MODIFY]** `tradingagents/dataflows/interface.py`
- **[MODIFY]** `tradingagents/default_config.py` (add cross_validation_tolerance)

### Implementation Details

1. **Import** vnstock and vietfin provider functions in `interface.py`
2. **Register** in VENDOR_METHODS:
   ```python
   "get_stock_data": {
       "vnstock": get_vnstock_stock_data,
       "vietfin": get_vietfin_stock_data,
       ...existing...
   },
   ```
3. **Add** new method entries for VN-specific methods:
   - `get_vnindex_data` (vnstock only)
   - `get_available_tickers` (vnstock only)
4. **Add** `cross_validation_tolerance` to DEFAULT_CONFIG

### UAT
- [ ] `route_to_vendor("get_stock_data", ...)` with market="VN" routes to vnstock
- [ ] Fallback from vnstock to vietfin works when vnstock fails
- [ ] US market unchanged (still routes to yfinance/alpha_vantage)
- [ ] New VN-specific methods callable via interface

---

## Dependency Order

```
Plan 1 (vnstock) ──┐
                    ├──► Plan 4 (Interface Registration)
Plan 2 (vietfin) ──┤
                    │
Plan 3 (Cross-val) ┘
```

Plans 1, 2, 3 can be implemented in parallel. Plan 4 depends on all three.

---

## Verification Plan

### Automated
```bash
python -c "from tradingagents.dataflows.vnstock_provider import get_stock_data; print(get_stock_data('FPT', '2025-01-01', '2025-03-31')[:200])"
python -c "from tradingagents.dataflows.vietfin_provider import get_stock_data; print(get_stock_data('VNM', '2025-01-01', '2025-03-31')[:200])"
python -c "from tradingagents.dataflows.cross_validator import validate_ohlcv; print(validate_ohlcv('FPT', '2025-01-01', '2025-03-31'))"
python -c "from tradingagents.dataflows.interface import route_to_vendor; print(type(route_to_vendor))"
```

### Syntax
```bash
python -m py_compile tradingagents/dataflows/vnstock_provider.py
python -m py_compile tradingagents/dataflows/vietfin_provider.py
python -m py_compile tradingagents/dataflows/cross_validator.py
python -m py_compile tradingagents/dataflows/interface.py
```
