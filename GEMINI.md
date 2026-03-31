<!-- GSD:project-start source:PROJECT.md -->
## Project

**TradingAgents — Vietnam Market & Enhanced Recommendations**

A multi-agent LLM framework for automated financial trading analysis that orchestrates specialized AI agents (analysts, researchers, debaters, portfolio managers) via LangGraph to produce trade recommendations. Currently supports US market data via yfinance and Alpha Vantage. Being extended to support the **Vietnamese stock market** (HOSE/VNIndex) with multiple free data sources, and enhanced to produce **price-targeted, time-horizon recommendations** across all markets.

**Core Value:** Deliver actionable, multi-source-validated trade signals with specific buy/sell price targets and time horizons — starting with the Vietnamese market — while always being transparent about which data sources are active and any failures.

### Constraints

- **Data sources**: Free APIs/libraries only — no paid subscriptions
- **Tech stack**: Must integrate into existing LangGraph/LangChain architecture
- **Vendor routing**: New sources must follow existing `interface.py` routing pattern
- **Backward compatibility**: US market support must continue working unchanged
- **Language**: Vietnamese news must be processable by the LLM agents (most modern LLMs handle Vietnamese)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

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
| Provider key | Backend | Notes |
|---|---|---|
| `openai` | `langchain-openai` | Default; supports reasoning_effort |
| `ollama` | `langchain-openai` | Uses OpenAI-compatible API; local models |
| `openrouter` | `langchain-openai` | Uses OpenAI-compatible API |
| `xai` | `langchain-openai` | Grok models |
| `anthropic` | `langchain-anthropic` | Supports effort parameter |
| `google` | `langchain-google-genai` | Supports thinking_level |
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
- **Data cache**: `tradingagents/dataflows/data_cache/` (auto-created on init)
- **Results output**: `eval_results/{ticker}/TradingAgentsStrategy_logs/` (created at runtime)
## Key Config Options (DEFAULT_CONFIG)
## Build & Packaging
- `setuptools` build system; `tradingagents*` and `cli*` packages included
- `cli/static/` directory included as package data
- Installable via `pip install .` or `uv pip install .`
- CLI command: `tradingagents` (maps to `cli/main.py:app`)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language Style
- **Python 3.10+** with type annotations (`typing`, `typing_extensions`, `__future__.annotations`)
- Uses `TypedDict` for state objects rather than dataclasses or Pydantic
- `Annotated[type, "description"]` used extensively for LangGraph state field documentation
- `from __future__ import annotations` used in `model_catalog.py` for forward references
## Naming Conventions
| Category | Convention | Example |
|---|---|---|
| Classes | PascalCase | `TradingAgentsGraph`, `FinancialSituationMemory` |
| Functions | snake_case | `create_market_analyst()`, `route_to_vendor()` |
| Constants | UPPER_SNAKE | `DEFAULT_CONFIG`, `MODEL_OPTIONS`, `VENDOR_METHODS` |
| Agent factory fns | `create_{role}` | `create_bull_researcher()`, `create_portfolio_manager()` |
| Tool functions | `get_{resource}` | `get_stock_data`, `get_indicators`, `get_news` |
| Config keys | lowercase snake string | `"deep_think_llm"`, `"max_debate_rounds"` |
| Graph node names | Title Case strings | `"Market Analyst"`, `"Bull Researcher"` |
| State fields | snake_case | `market_report`, `final_trade_decision` |
| Private methods | `_single_underscore` | `_get_provider_kwargs()`, `_rebuild_index()` |
## Module / File Organization Patterns
- **Factory pattern** throughout: `create_llm_client()`, `create_market_analyst()`, etc. return configured instances
- **Single-responsibility** per file — each agent type has its own file
- **Group by role** — agents split into `analysts/`, `researchers/`, `managers/`, `risk_mgmt/`, `trader/`
- `__init__.py` files export all public symbols with star imports (`from .module import *`)
- `agents/__init__.py` is the aggregation point — exports all `create_*` factory functions
## Agent Definition Pattern
## LLM Invocation Pattern
- All agents pass tuples (not `SystemMessage`/`HumanMessage` objects) to `.invoke()`
- `.content` is always accessed directly (no structured output used in agents)
- Memory retrieval: `memory.get_memories(situation, n_matches=N)` inserted into system prompt context
## Tool Function Pattern
- All tool functions use `Annotated` parameter descriptions (LangChain auto-generates tool schemas)
- Tools return strings (the agent parses these raw strings in its context)
- Tools route through `interface.route_to_vendor()`
## Error Handling
- `AlphaVantageRateLimitError` — custom exception for AV rate limits; caught in `route_to_vendor()` to trigger fallback
- Vendor fallback chain: primary vendor → all other available vendors
- `ValueError` raised for: unknown providers, unsupported methods, missing analysts
- No global error handling wrapper observed — errors propagate naturally from LangGraph
- Memory system returns `[]` (empty list) on empty index rather than raising
## State Updates
- Each agent returns a **partial dict** with only the fields it updates
- LangGraph merges updates automatically into `AgentState`
- `create_msg_delete()` returns a function that clears all messages and adds a `HumanMessage("Continue")` placeholder — required for Anthropic compatibility (Anthropic requires messages to start with user)
## Configuration Pattern
## Internationalization
- `output_language` config field — agents call `get_language_instruction()` which returns empty string for English or a language directive string
- Only user-facing agents (analysts, portfolio manager) use `get_language_instruction()`
- Internal debate agents always use English for reasoning quality
## CLI Patterns
- Built with **Typer** — commands defined as decorated functions
- Interactive prompts use **questionary** for multi-choice, confirmation
- Output formatted with **rich** tables, panels, and progress indicators
- `stats_handler.py` implements `BaseCallbackHandler` for LangChain callback tracking
## Documentation Style
- Module/class/function docstrings present on most public items
- Inline comments used for configuration sections
- Type hints on all function signatures in core modules
- `TODO.md` in `llm_clients/` for tracking known issues
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
## High-Level Data Flow
```
```
## Architectural Patterns
### 1. StateGraph (LangGraph)
- All agent state flows through a single `AgentState` TypedDict (defined in `tradingagents/agents/utils/agent_states.py`)
- State is passed immutably between nodes; each node returns partial state updates
- `InvestDebateState` and `RiskDebateState` are nested state objects for debate loops
### 2. Conditional Routing (Debate Loops)
- `ConditionalLogic` class (`tradingagents/graph/conditional_logic.py`) contains edge condition functions
- Debate rounds controlled by counters in state (`count`) vs config limits
- Analysts use tool-call → tool-response loops with `should_continue_{analyst}` conditions
### 3. Separation of Concerns (Graph Modules)
```
```
### 4. LLM Client Factory Pattern
- `tradingagents/llm_clients/factory.py` — `create_llm_client(provider, model, base_url, **kwargs)` 
- All clients extend `BaseLLMClient` (`base_client.py`)
- Each client wraps a specific LangChain chat model and exposes `.get_llm()` returning the LangChain LLM object
### 5. Vendor Routing / Strategy Pattern
- `tradingagents/dataflows/interface.py` acts as router
- `VENDOR_METHODS` dict maps `method_name → {vendor_name → impl_function}`
- `route_to_vendor(method, *args, **kwargs)` dispatches dynamically with fallback
### 6. BM25 Agent Memory
- `FinancialSituationMemory` (`agents/utils/memory.py`) — in-memory BM25 index
- Separate memory instances per role: `bull_memory`, `bear_memory`, `trader_memory`, `invest_judge_memory`, `portfolio_manager_memory`
- `reflect_and_remember()` on `TradingAgentsGraph` runs post-trade reflection to update all memories
- Memory retrieved as context for each agent on next `propagate()` call
### 7. Tool Nodes (LangChain ToolNode)
- Tools are wrapped LangChain-compatible functions in `agents/utils/*_tools.py`
- `TradingAgentsGraph._create_tool_nodes()` creates per-analyst `ToolNode` objects
- Tool call routing: `agent → ToolNode → agent` (LangGraph built-in pattern)
## Two-Tier LLM Strategy
- **quick_thinking_llm**: Used by analysts, researchers, trader — speed-optimized model
- **deep_thinking_llm**: Used by Research Manager and Portfolio Manager (judges) — quality-optimized model, reasoning models supported
## Entry Points
| Entry point | Path | Description |
|---|---|---|
| Script | `main.py` | Direct usage example |
| CLI | `cli/main.py` | Interactive `tradingagents` CLI |
| API | `TradingAgentsGraph` class | Programmatic Python API |
## Callbacks / Observability
- `TradingAgentsGraph` accepts `callbacks` list (LangChain callbacks)
- `cli/stats_handler.py` implements callback for tracking LLM token usage / cost
- Each `propagate()` call logs full state to `eval_results/{ticker}/.../*.json`
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
