import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # Market configuration
    "market": os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US"),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "gpt-5.4",
    "quick_think_llm": "gpt-5.4-mini",
    "backend_url": "https://api.openai.com/v1",
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    "anthropic_effort": None,           # "high", "medium", "low"
    # Output language for analyst reports and final decision
    # Internal agent debate stays in English for reasoning quality
    "output_language": "English",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # US: yfinance, alpha_vantage | VN: vnstock, vietfin
        "technical_indicators": "yfinance",  # US: yfinance, alpha_vantage | VN: vnstock
        "fundamental_data": "yfinance",      # US: yfinance, alpha_vantage | VN: vnstock, vietfin
        "news_data": "yfinance",             # US: yfinance, alpha_vantage | VN: vnstock (Phase 5)
        "market_data": "vnstock",            # VN-specific: vnstock
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
    },
    # Cross-validation tolerance for comparing VN data sources
    # 0.01 = 1% price difference threshold
    "cross_validation_tolerance": 0.01,
}
