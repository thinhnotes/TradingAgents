# STRUCTURE.md — Directory Layout & Organization

## Top-Level Layout

```
TradingAgents/
├── main.py                    # Quick-start usage example
├── test.py                    # Ad-hoc test script
├── pyproject.toml             # Package config, dependencies, build system
├── requirements.txt           # Single-line: "." (installs project itself)
├── uv.lock                    # uv lockfile (670KB — full dependency tree)
├── .env.example               # Environment variable template
├── .gitignore                 # Standard Python + results ignores
├── LICENSE                    # Open source license
├── README.md                  # Project documentation (11KB)
│
├── tradingagents/             # Main Python package
├── cli/                       # CLI package
├── tests/                     # Unit tests
└── assets/                    # Static assets (images, etc.)
```

## `tradingagents/` — Core Package

```
tradingagents/
├── __init__.py                # Package init
├── default_config.py          # DEFAULT_CONFIG dict — all runtime settings
│
├── graph/                     # LangGraph orchestration layer
│   ├── __init__.py
│   ├── trading_graph.py       # TradingAgentsGraph — main public API class (11KB)
│   ├── setup.py               # GraphSetup — builds StateGraph nodes/edges (8KB)
│   ├── conditional_logic.py   # ConditionalLogic — edge routing conditions (2.8KB)
│   ├── propagation.py         # Propagator — state init, graph execution (2.4KB)
│   ├── reflection.py          # Reflector — post-trade memory updates (6KB)
│   └── signal_processing.py   # SignalProcessor — parse decision string (1.1KB)
│
├── agents/                    # Agent definitions
│   ├── __init__.py            # Exports all create_*() factory functions (1.5KB)
│   │
│   ├── analysts/              # Analyst agents (generate reports from data)
│   │   ├── fundamentals_analyst.py   # Fundamentals analysis agent
│   │   ├── market_analyst.py         # Market/technical analysis agent (6.3KB)
│   │   ├── news_analyst.py           # News analysis agent
│   │   └── social_media_analyst.py   # Social/sentiment analysis agent
│   │
│   ├── researchers/           # Investment thesis debate agents
│   │   ├── bull_researcher.py         # Bullish position researcher
│   │   └── bear_researcher.py         # Bearish position researcher
│   │
│   ├── managers/              # Judge/decision agents
│   │   ├── research_manager.py        # Investment debate judge (deep LLM)
│   │   └── portfolio_manager.py       # Risk debate judge / final decision (deep LLM)
│   │
│   ├── risk_mgmt/             # Risk analysis debate agents
│   │   ├── aggressive_debator.py
│   │   ├── conservative_debator.py
│   │   └── neutral_debator.py
│   │
│   ├── trader/                # Trader agent
│   │   └── trader.py                  # Converts research into trade plan
│   │
│   └── utils/                 # Shared agent utilities
│       ├── agent_states.py            # AgentState, InvestDebateState, RiskDebateState TypedDicts
│       ├── agent_utils.py             # create_msg_delete(), get_language_instruction(), build_instrument_context()
│       ├── memory.py                  # FinancialSituationMemory (BM25-based)
│       ├── core_stock_tools.py        # get_stock_data tool
│       ├── technical_indicators_tools.py  # get_indicators tool
│       ├── fundamental_data_tools.py  # get_fundamentals, balance_sheet, cashflow, income_statement tools
│       └── news_data_tools.py         # get_news, get_global_news, get_insider_transactions tools
│
├── dataflows/                 # Data vendor abstraction layer
│   ├── __init__.py
│   ├── config.py              # Global config getter/setter for dataflows
│   ├── interface.py           # Vendor routing: TOOLS_CATEGORIES, VENDOR_METHODS, route_to_vendor() (5.6KB)
│   ├── utils.py               # Shared data utilities
│   ├── y_finance.py           # yfinance implementations (17KB — largest file)
│   ├── yfinance_news.py       # yfinance news scraping (6.7KB)
│   ├── stockstats_utils.py    # stockstats technical indicator helpers
│   ├── alpha_vantage.py       # Alpha Vantage router (0.3KB)
│   ├── alpha_vantage_common.py      # Shared AV HTTP client + rate limit error
│   ├── alpha_vantage_stock.py
│   ├── alpha_vantage_indicator.py   # (11KB — largest AV file)
│   ├── alpha_vantage_fundamentals.py
│   └── alpha_vantage_news.py
│
└── llm_clients/               # LLM provider abstraction
    ├── __init__.py            # Exports create_llm_client()
    ├── base_client.py         # BaseLLMClient abstract class
    ├── factory.py             # create_llm_client() factory function
    ├── openai_client.py       # OpenAI / Ollama / OpenRouter / xAI
    ├── anthropic_client.py    # Anthropic Claude
    ├── google_client.py       # Google Gemini (NormalizedChatGoogleGenerativeAI)
    ├── model_catalog.py       # MODEL_OPTIONS dict + helpers (4.6KB)
    ├── validators.py          # validate_model() — checks model name against catalog
    └── TODO.md                # Known issues list
```

## `cli/` — CLI Package

```
cli/
├── __init__.py
├── main.py                    # Typer CLI app — primary interactive interface (50KB — largest file in project)
├── config.py                  # CLI config constants
├── announcements.py           # In-app announcements (1.6KB)
├── models.py                  # CLI Pydantic models
├── stats_handler.py           # LLM stats/cost callback handler (2.4KB)
├── utils.py                   # CLI utilities (10.8KB)
└── static/                    # Static assets bundled with CLI
```

## `tests/` — Test Suite

```
tests/
├── test_google_api_key.py          # Google client API key handling
├── test_model_validation.py        # Model catalog + validation logic
└── test_ticker_symbol_handling.py  # Ticker symbol edge cases
```

## Key Naming Conventions

- Agent factory functions: `create_{role}()` — e.g., `create_market_analyst()`, `create_bull_researcher()`
- Graph node names: Human-readable strings — `"Market Analyst"`, `"Bull Researcher"`, `"Portfolio Manager"`
- Tool functions: `get_{data_type}` — e.g., `get_stock_data`, `get_indicators`, `get_news`
- Vendor implementations: `get_{domain}_{vendor}` — e.g., `get_news_yfinance`, `get_YFin_data_online`
- State fields: snake_case — `market_report`, `investment_debate_state`, `final_trade_decision`
- Config keys: snake_case strings — `"deep_think_llm"`, `"max_debate_rounds"`

## Runtime-Created Directories

- `tradingagents/dataflows/data_cache/` — created on `TradingAgentsGraph` init
- `eval_results/{ticker}/TradingAgentsStrategy_logs/` — created on `propagate()` call
- `results/` — default results dir (configurable via `TRADINGAGENTS_RESULTS_DIR`)
