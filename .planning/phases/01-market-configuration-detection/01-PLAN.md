---
wave: 1
depends_on: []
files_modified:
  - tradingagents/default_config.py
  - tradingagents/dataflows/market_config.py
requirements_addressed: [MKTC-01, MKTC-02, MKTC-05]
autonomous: true
---

# Plan 01: Market Configuration Foundation

<objective>
Add `market` field to the config system and create a `market_config.py` module that provides market metadata (currency, exchange, trading hours, settlement cycle, price unit) for US and VN markets. This establishes the data foundation so all downstream components can be market-aware.
</objective>

<must_haves>
- Config `market` field defaults to `"US"` (backward compatible)
- Environment variable `TRADINGAGENTS_DEFAULT_MARKET` overrides default
- Market metadata module provides currency, exchange name, trading hours for US and VN
- No existing behavior changes for US market
</must_haves>

## Tasks

### Task 1: Add market field to DEFAULT_CONFIG

<read_first>
- tradingagents/default_config.py
</read_first>

<action>
In `tradingagents/default_config.py`, add the following field to `DEFAULT_CONFIG` dict, after the `"data_cache_dir"` entry and before the `# LLM settings` comment:

```python
# Market configuration
"market": os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US"),
```

This adds market selection with environment variable override. Default is `"US"` for backward compatibility.
</action>

<acceptance_criteria>
- `default_config.py` contains `"market": os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US")`
- `DEFAULT_CONFIG["market"]` evaluates to `"US"` when env var is not set
</acceptance_criteria>

### Task 2: Create market_config.py module

<read_first>
- tradingagents/default_config.py
- tradingagents/dataflows/config.py
</read_first>

<action>
Create new file `tradingagents/dataflows/market_config.py` with exactly this content:

```python
"""Market-specific configuration and metadata for supported markets."""

from typing import Dict, Any

# Market metadata for supported markets
MARKET_METADATA: Dict[str, Dict[str, Any]] = {
    "US": {
        "currency": "USD",
        "currency_symbol": "$",
        "exchange": "NYSE/NASDAQ",
        "trading_hours": "09:30-16:00 ET",
        "settlement": "T+1",
        "price_unit": 1,
        "price_format": "${:,.2f}",
        "supported_vendors": ["yfinance", "alpha_vantage"],
    },
    "VN": {
        "currency": "VND",
        "currency_symbol": "₫",
        "exchange": "HOSE",
        "trading_hours": "09:00-15:00 ICT",
        "settlement": "T+2",
        "price_unit": 1000,
        "price_format": "{:,.0f} VND",
        "supported_vendors": ["vnstock", "vietfin", "yfinance"],
    },
}

SUPPORTED_MARKETS = list(MARKET_METADATA.keys())


def get_market_metadata(market: str) -> Dict[str, Any]:
    """Get metadata for a specific market.
    
    Args:
        market: Market code ('US' or 'VN').
        
    Returns:
        Dictionary with market metadata.
        
    Raises:
        ValueError: If market is not supported.
    """
    market = market.upper()
    if market not in MARKET_METADATA:
        raise ValueError(
            f"Unsupported market '{market}'. Supported: {SUPPORTED_MARKETS}"
        )
    return MARKET_METADATA[market].copy()


def get_market_currency(market: str) -> str:
    """Get the currency code for a market."""
    return get_market_metadata(market)["currency"]


def get_market_vendors(market: str) -> list:
    """Get the supported data vendors for a market."""
    return get_market_metadata(market)["supported_vendors"]


def is_valid_market(market: str) -> bool:
    """Check if a market code is valid."""
    return market.upper() in MARKET_METADATA
```
</action>

<acceptance_criteria>
- File `tradingagents/dataflows/market_config.py` exists
- `market_config.py` contains `MARKET_METADATA` dict with "US" and "VN" keys
- `market_config.py` contains `get_market_metadata` function
- `market_config.py` contains `get_market_currency` function
- `market_config.py` contains `get_market_vendors` function
- `market_config.py` contains `is_valid_market` function
- `MARKET_METADATA["VN"]["currency"]` equals `"VND"`
- `MARKET_METADATA["US"]["currency"]` equals `"USD"`
</acceptance_criteria>

## Verification

```bash
python -c "from tradingagents.default_config import DEFAULT_CONFIG; assert DEFAULT_CONFIG['market'] == 'US', 'market default wrong'; print('✓ Config market default OK')"
python -c "from tradingagents.dataflows.market_config import get_market_metadata, is_valid_market; assert is_valid_market('VN'); assert is_valid_market('US'); m = get_market_metadata('VN'); assert m['currency'] == 'VND'; print('✓ Market metadata OK')"
```

---
*Phase: 01-market-configuration-detection*
