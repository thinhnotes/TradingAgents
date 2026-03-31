# CONVENTIONS.md — Code Style & Patterns

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

All agents follow the same structure:

```python
def create_{agent_name}(llm, memory=None) -> Callable:
    """Docstring describing the agent's role."""
    
    system_prompt = """..."""  # Inline system prompt string
    
    def agent_function(state: AgentState) -> dict:
        """Inner agent function that processes state."""
        # 1. Extract relevant fields from state
        # 2. Optionally retrieve memory
        # 3. Build messages list
        # 4. Call llm.invoke(messages)
        # 5. Return state update dict
        return {"field_name": result}
    
    return agent_function
```

## LLM Invocation Pattern

```python
# Standard pattern across all agents:
messages = [
    ("system", system_prompt),
    ("human", f"Context: {context}\n\nTask: {task}"),
]
result = llm.invoke(messages).content
```

- All agents pass tuples (not `SystemMessage`/`HumanMessage` objects) to `.invoke()`
- `.content` is always accessed directly (no structured output used in agents)
- Memory retrieval: `memory.get_memories(situation, n_matches=N)` inserted into system prompt context

## Tool Function Pattern

```python
from langchain_core.tools import tool  # (implied via Annotated usage)
from typing import Annotated

def get_stock_data(
    ticker: Annotated[str, "Stock ticker symbol"],
    start_date: Annotated[str, "Start date YYYY-MM-DD"],
    end_date: Annotated[str, "End date YYYY-MM-DD"],
) -> str:
    """Docstring used as tool description for LLM."""
    return route_to_vendor("get_stock_data", ticker, start_date, end_date)
```

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

```python
# Accessing config in dataflows:
from tradingagents.dataflows.config import get_config
config = get_config()
vendor = config.get("data_vendors", {}).get("core_stock_apis", "yfinance")

# Setting config (done once at graph init):
from tradingagents.dataflows.config import set_config
set_config(self.config)  # stores globally in dataflows.config module
```

Config is a module-level global in `dataflows/config.py` — initialized once per graph instance.

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
