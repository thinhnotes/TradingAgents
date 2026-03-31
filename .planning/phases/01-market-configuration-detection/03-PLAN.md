---
wave: 2
depends_on: [01, 02]
files_modified:
  - tradingagents/dataflows/interface.py
requirements_addressed: [MKTC-04]
autonomous: true
---

# Plan 03: Market-Aware Vendor Routing

<objective>
Update `interface.py` vendor routing to be market-aware. When the configured market is "VN", the system will route to VN-specific vendors (to be implemented in Phase 2). For now, create the routing infrastructure and market-based vendor selection without actual VN vendor implementations.
</objective>

<must_haves>
- `route_to_vendor()` reads market from config to determine vendor chain
- VN market routing infrastructure ready (actual implementations added in Phase 2)
- US market routing unchanged
- Market-specific vendor fallback chains
</must_haves>

## Tasks

### Task 1: Add market-aware vendor routing to interface.py

<read_first>
- tradingagents/dataflows/interface.py
- tradingagents/dataflows/market_config.py
- tradingagents/dataflows/config.py
</read_first>

<action>
In `tradingagents/dataflows/interface.py`, make these changes:

1. Add import at top (after existing imports):
```python
from .market_config import get_market_metadata, get_market_vendors
```

2. Add VN vendor placeholders to `VENDOR_LIST`:
```python
VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "vnstock",
    "vietfin",
]
```

3. Replace the `get_vendor()` function with a market-aware version:

```python
def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Market-aware: uses VN-specific vendors when market is VN.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()
    market = config.get("market", "US").upper()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # For VN market, use VN-specific default vendors
    if market == "VN":
        vn_defaults = {
            "core_stock_apis": "vnstock",
            "technical_indicators": "vnstock",
            "fundamental_data": "vnstock",
            "news_data": "vnstock",
        }
        return config.get("data_vendors", {}).get(category, vn_defaults.get(category, "vnstock"))

    # Fall back to category-level configuration (US market default)
    return config.get("data_vendors", {}).get(category, "yfinance")
```

4. Update `route_to_vendor()` to handle market-specific fallback and provide a more informative error:

```python
def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with market-aware fallback."""
    config = get_config()
    market = config.get("market", "US").upper()
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Build market-aware fallback chain
    market_vendors = get_market_vendors(market)
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    
    # Priority: primary configured → market-specific → all available
    fallback_vendors = primary_vendors.copy()
    for vendor in market_vendors:
        if vendor not in fallback_vendors and vendor in all_available_vendors:
            fallback_vendors.append(vendor)
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    last_error = None
    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        impl_func = vendor_impl[0] if isinstance(vendor_impl, list) else vendor_impl

        try:
            return impl_func(*args, **kwargs)
        except AlphaVantageRateLimitError:
            last_error = f"Rate limit on {vendor}"
            continue
        except Exception as e:
            last_error = f"{vendor}: {str(e)}"
            continue  # Any error triggers fallback for VN market

    raise RuntimeError(
        f"No available vendor for '{method}' in market '{market}'. "
        f"Tried: {fallback_vendors}. Last error: {last_error}"
    )
```
</action>

<acceptance_criteria>
- `interface.py` contains `from .market_config import get_market_metadata, get_market_vendors`
- `interface.py` `VENDOR_LIST` contains `"vnstock"` and `"vietfin"`
- `get_vendor()` function checks `config.get("market", "US")` 
- `get_vendor()` returns `"vnstock"` for VN market categories
- `route_to_vendor()` builds market-aware fallback chain using `get_market_vendors(market)`
- `route_to_vendor()` catches generic `Exception` (not just `AlphaVantageRateLimitError`) for broader fallback
- Error message includes market name and tried vendors
</acceptance_criteria>

## Verification

```bash
python -c "
from tradingagents.dataflows.interface import get_vendor, VENDOR_LIST
from tradingagents.dataflows.config import set_config

# Test US market (default)
set_config({'market': 'US'})
assert get_vendor('core_stock_apis') == 'yfinance', 'US should default to yfinance'

# Test VN market
set_config({'market': 'VN'})
assert get_vendor('core_stock_apis') == 'vnstock', f'VN should default to vnstock, got {get_vendor(\"core_stock_apis\")}'

# Test vendor list
assert 'vnstock' in VENDOR_LIST
assert 'vietfin' in VENDOR_LIST

print('✓ Market-aware vendor routing OK')
"
```

---
*Phase: 01-market-configuration-detection*
