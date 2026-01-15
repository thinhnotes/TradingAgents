import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # Market configuration
    # Options: "us" (US market - NYSE, NASDAQ), "vn" (Vietnam market - HOSE, HNX, UPCOM)
    "market": "us",
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: yfinance, alpha_vantage, vnstock, local
        "technical_indicators": "yfinance",  # Options: yfinance, alpha_vantage, vnstock, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, vnstock, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, vnstock, local
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },
}

# Vietnam market configuration preset
# Use this for trading Vietnamese stocks (HOSE, HNX, UPCOM exchanges)
VN_MARKET_CONFIG = {
    "market": "vn",
    "data_vendors": {
        "core_stock_apis": "vnstock",        # Vietnam stock data via vnstock library
        "technical_indicators": "vnstock",   # Technical indicators calculated from vnstock data
        "fundamental_data": "vnstock",       # Vietnamese company financials via vnstock
        "news_data": "vnstock",              # Vietnamese news from CafeF, Vietstock, VnExpress
    },
}

# Vietnam exchange definitions
VN_EXCHANGES = {
    "HOSE": {
        "name": "Ho Chi Minh Stock Exchange",
        "price_limit_percent": 7.0,    # ±7% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
    "HNX": {
        "name": "Hanoi Stock Exchange",
        "price_limit_percent": 10.0,   # ±10% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
    "UPCOM": {
        "name": "Unlisted Public Company Market",
        "price_limit_percent": 15.0,   # ±15% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
}

# Vietnam market trading rules
VN_MARKET_RULES = {
    "settlement_days": 2.5,            # T+2.5 settlement (can sell morning of T+3)
    "default_lot_size": 100,           # Standard lot size for all exchanges
    "odd_lot_allowed": False,          # Odd lots require separate order book
    "currency": "VND",                 # Vietnamese Dong
    "market_indices": ["VN-Index", "HNX-Index", "UPCOM-Index"],
}


def get_market_config(market: str = "us") -> dict:
    """
    Get configuration for the specified market.

    Args:
        market: Market identifier ("us" or "vn")

    Returns:
        dict: Configuration dictionary with market-specific settings merged
    """
    config = DEFAULT_CONFIG.copy()

    if market.lower() == "vn":
        # Apply Vietnam market overrides
        config["market"] = "vn"
        config["data_vendors"] = VN_MARKET_CONFIG["data_vendors"].copy()

    return config
