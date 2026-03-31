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
