from typing import Annotated

# Import from vendor-specific modules
from .y_finance import (
    get_YFin_data_online,
    get_stock_stats_indicators_window,
    get_fundamentals as get_yfinance_fundamentals,
    get_balance_sheet as get_yfinance_balance_sheet,
    get_cashflow as get_yfinance_cashflow,
    get_income_statement as get_yfinance_income_statement,
    get_insider_transactions as get_yfinance_insider_transactions,
)
from .yfinance_news import get_news_yfinance, get_global_news_yfinance
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news,
)
from .alpha_vantage_common import AlphaVantageRateLimitError
from .vnstock_provider import (
    get_stock_data as get_vnstock_stock_data,
    get_fundamentals as get_vnstock_fundamentals,
    get_balance_sheet as get_vnstock_balance_sheet,
    get_cashflow as get_vnstock_cashflow,
    get_income_statement as get_vnstock_income_statement,
    get_insider_transactions as get_vnstock_insider_transactions,
    get_news as get_vnstock_news,
    get_global_news as get_vnstock_global_news,
    get_vnindex_data,
    get_available_tickers as get_vnstock_available_tickers,
)
from .vietfin_provider import (
    get_stock_data as get_vietfin_stock_data,
    get_fundamentals as get_vietfin_fundamentals,
    get_balance_sheet as get_vietfin_balance_sheet,
    get_cashflow as get_vietfin_cashflow,
    get_income_statement as get_vietfin_income_statement,
    get_insider_transactions as get_vietfin_insider_transactions,
    get_news as get_vietfin_news,
    get_global_news as get_vietfin_global_news,
)

# Configuration and routing logic
from .config import get_config
from .market_config import get_market_vendors

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV stock price data",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "News and insider data",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_transactions",
        ]
    },
    "market_data": {
        "description": "Market index and listing data",
        "tools": [
            "get_vnindex_data",
            "get_available_tickers",
        ]
    }
}

VENDOR_LIST = [
    "yfinance",
    "alpha_vantage",
    "vnstock",
    "vietfin",
]

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
        "vnstock": get_vnstock_stock_data,
        "vietfin": get_vietfin_stock_data,
    },
    # technical_indicators
    "get_indicators": {
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "yfinance": get_yfinance_fundamentals,
        "vnstock": get_vnstock_fundamentals,
        "vietfin": get_vietfin_fundamentals,
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
        "vnstock": get_vnstock_balance_sheet,
        "vietfin": get_vietfin_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "yfinance": get_yfinance_cashflow,
        "vnstock": get_vnstock_cashflow,
        "vietfin": get_vietfin_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "yfinance": get_yfinance_income_statement,
        "vnstock": get_vnstock_income_statement,
        "vietfin": get_vietfin_income_statement,
    },
    # news_data
    "get_news": {
        "alpha_vantage": get_alpha_vantage_news,
        "yfinance": get_news_yfinance,
        "vnstock": get_vnstock_news,
        "vietfin": get_vietfin_news,
    },
    "get_global_news": {
        "yfinance": get_global_news_yfinance,
        "alpha_vantage": get_alpha_vantage_global_news,
        "vnstock": get_vnstock_global_news,
        "vietfin": get_vietfin_global_news,
    },
    "get_insider_transactions": {
        "alpha_vantage": get_alpha_vantage_insider_transactions,
        "yfinance": get_yfinance_insider_transactions,
        "vnstock": get_vnstock_insider_transactions,
        "vietfin": get_vietfin_insider_transactions,
    },
    # market_data (VN-specific)
    "get_vnindex_data": {
        "vnstock": get_vnindex_data,
    },
    "get_available_tickers": {
        "vnstock": get_vnstock_available_tickers,
    },
}

def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")

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
            "market_data": "vnstock",
        }
        return config.get("data_vendors", {}).get(category, vn_defaults.get(category, "vnstock"))

    # Fall back to category-level configuration (US market default)
    return config.get("data_vendors", {}).get(category, "yfinance")

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

    # Priority: primary configured -> market-specific -> all available
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
            continue  # Any error triggers fallback

    raise RuntimeError(
        f"No available vendor for '{method}' in market '{market}'. "
        f"Tried: {fallback_vendors}. Last error: {last_error}"
    )