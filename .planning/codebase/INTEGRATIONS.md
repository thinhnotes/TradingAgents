# INTEGRATIONS.md — External Services & APIs

## Data Vendors

### yfinance (Primary / Default)
- **What**: Yahoo Finance Python wrapper — provides OHLCV, fundamentals, news, insider transactions
- **Authentication**: None required (public API)
- **Implementation**: `tradingagents/dataflows/y_finance.py`, `tradingagents/dataflows/yfinance_news.py`
- **Functions exposed**:
  - `get_YFin_data_online(ticker, start_date, end_date)` — OHLCV
  - `get_stock_stats_indicators_window(ticker, ...)` — Technical indicators via `stockstats`
  - `get_fundamentals(ticker)`, `get_balance_sheet(ticker)`, `get_cashflow(ticker)`, `get_income_statement(ticker)`
  - `get_insider_transactions(ticker)`
  - `get_news_yfinance(ticker, ...)`, `get_global_news_yfinance(...)` — news scraping

### Alpha Vantage (Alternative vendor)
- **What**: Premium financial data API
- **Authentication**: `ALPHA_VANTAGE_API_KEY` environment variable (implied)
- **Rate limiting**: `AlphaVantageRateLimitError` triggers automatic fallback to yfinance in `interface.py`
- **Implementation**: `tradingagents/dataflows/alpha_vantage_*.py` (multiple files):
  - `alpha_vantage_common.py` — shared HTTP client, rate limit error class
  - `alpha_vantage_stock.py` — OHLCV
  - `alpha_vantage_indicator.py` — Technical indicators
  - `alpha_vantage_fundamentals.py` — Company fundamentals
  - `alpha_vantage_news.py` — News data

## LLM Providers

All LLMs accessed via LangChain wrappers. Provider keys read from environment:

| Provider | Env var | Client class |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OpenAIClient` (`langchain-openai`) |
| Anthropic | `ANTHROPIC_API_KEY` | `AnthropicClient` (`langchain-anthropic`) |
| Google | `GOOGLE_API_KEY` | `GoogleClient` (`langchain-google-genai`) |
| xAI (Grok) | `XAI_API_KEY` | `OpenAIClient` with xai base_url |
| OpenRouter | `OPENROUTER_API_KEY` | `OpenAIClient` with openrouter base_url |
| Ollama | None (local) | `OpenAIClient` with local base_url |

### Custom base_url Support
All clients accept `base_url` override for self-hosted / proxy deployments (configured via `config["backend_url"]`).

## Vendor Abstraction / Routing

`tradingagents/dataflows/interface.py` implements vendor-agnostic routing:

```python
# Category-level routing (default)
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "yfinance",
}

# Tool-level override (takes precedence over category)
config["tool_vendors"] = {
    "get_stock_data": "alpha_vantage",  # Example override
}
```

Fallback chain: if primary vendor fails with `AlphaVantageRateLimitError`, automatically falls back to next available vendor.

## Persistent Storage

### Redis
- **Listed as dependency** (`redis>=6.2.0`) but usage appears limited/optional
- No clear in-code usage found in core dataflows (may be for caching in some deployments)

### File System
- `tradingagents/dataflows/data_cache/` — local data caching directory (auto-created)
- `eval_results/{ticker}/TradingAgentsStrategy_logs/full_states_log_{date}.json` — trade decision logs written on each `propagate()` call

## CLI / Web Interface

`cli/main.py` — Full-featured CLI built with Typer:
- Interactive session UI using `questionary` + `rich`
- `cli/static/` — static assets for the CLI (bundled in package)
- `cli/announcements.py` — in-app announcement system
- `cli/stats_handler.py` — LLM usage / cost tracking (callbacks)
- `cli/utils.py` — Helper utilities for the CLI (~10KB, significant file)

## No External SaaS Integrations
The project does not integrate with any trading execution APIs (no broker connections), alerting systems, or cloud services beyond the LLM APIs listed above.
