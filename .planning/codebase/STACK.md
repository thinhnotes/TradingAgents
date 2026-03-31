# STACK.md — Technology Stack

## Language & Runtime

- **Language**: Python 3.10+ (required via `pyproject.toml`)
- **Package manager**: `uv` (lockfile: `uv.lock`) — fast pip replacement; `setuptools>=61.0` as build backend
- **Entry point**: `main.py` (script), `cli.main:app` (installed CLI command `tradingagents`)
- **Version**: `0.2.3` (see `pyproject.toml`)

## Core Frameworks

| Framework | Version | Role |
|---|---|---|
| `langgraph` | >=0.4.8 | Agent workflow graph orchestration |
| `langchain-core` | >=0.3.81 | LLM abstraction, message types, tool nodes |
| `langchain-openai` | >=0.3.23 | OpenAI / Ollama / OpenRouter / xAI client |
| `langchain-anthropic` | >=0.3.15 | Anthropic Claude client |
| `langchain-google-genai` | >=2.1.5 | Google Gemini client |
| `langchain-experimental` | >=0.3.4 | Experimental LC components |
| `typer` | >=0.21.0 | CLI framework |
| `questionary` | >=2.1.0 | Interactive CLI prompts |
| `rich` | >=14.0.0 | Terminal formatting / pretty-print |

## LLM Provider Support

Supported providers (factory pattern in `tradingagents/llm_clients/factory.py`):

| Provider key | Backend | Notes |
|---|---|---|
| `openai` | `langchain-openai` | Default; supports reasoning_effort |
| `ollama` | `langchain-openai` | Uses OpenAI-compatible API; local models |
| `openrouter` | `langchain-openai` | Uses OpenAI-compatible API |
| `xai` | `langchain-openai` | Grok models |
| `anthropic` | `langchain-anthropic` | Supports effort parameter |
| `google` | `langchain-google-genai` | Supports thinking_level |

Provider-specific thinking/reasoning kwargs are routed in `TradingAgentsGraph._get_provider_kwargs()`.

## Data & Financial Libraries

| Library | Role |
|---|---|
| `yfinance>=0.2.63` | Primary data vendor — OHLCV, fundamentals, news, insider transactions |
| `pandas>=2.3.0` | Data manipulation for financial data |
| `stockstats>=0.6.5` | Technical indicator computation |
| `backtrader>=1.9.78.123` | Backtesting framework (imported as dependency) |
| `rank-bm25>=0.2.2` | BM25 lexical retrieval for agent memory system |
| `pytz>=2025.2` | Timezone handling |
| `parsel>=1.10.0` | HTML/XML parsing for web scraping |

## Caching & Infrastructure

| Library | Role |
|---|---|
| `redis>=6.2.0` | Listed as dependency (imported in dataflows) |
| `requests>=2.32.4` | HTTP requests for Alpha Vantage API calls |
| `tqdm>=4.67.1` | Progress bars |
| `typing-extensions>=4.14.0` | Extended type hints |

## Configuration

- **Config system**: Dictionary-based (`DEFAULT_CONFIG` in `tradingagents/default_config.py`)
- **Environment variables**: `.env` file loaded via `python-dotenv` (see `main.py`)
  - `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`
  - `TRADINGAGENTS_RESULTS_DIR` — results output directory (default: `./results`)
- **Data cache**: `tradingagents/dataflows/data_cache/` (auto-created on init)
- **Results output**: `eval_results/{ticker}/TradingAgentsStrategy_logs/` (created at runtime)

## Key Config Options (DEFAULT_CONFIG)

```python
{
    "llm_provider": "openai",           # LLM backend
    "deep_think_llm": "gpt-5.4",        # Used by: Research Manager, Portfolio Manager
    "quick_think_llm": "gpt-5.4-mini",  # Used by: all analyst agents, Trader, Reflector
    "max_debate_rounds": 1,             # Investment debate rounds
    "max_risk_discuss_rounds": 1,       # Risk debate rounds
    "max_recur_limit": 100,             # LangGraph recursion limit
    "output_language": "English",       # User-facing agent output language
    "data_vendors": { ... },            # Per-category vendor routing
    "tool_vendors": { ... },            # Per-tool override (takes precedence)
}
```

## Build & Packaging

- `setuptools` build system; `tradingagents*` and `cli*` packages included
- `cli/static/` directory included as package data
- Installable via `pip install .` or `uv pip install .`
- CLI command: `tradingagents` (maps to `cli/main.py:app`)
