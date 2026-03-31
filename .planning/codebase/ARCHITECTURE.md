# ARCHITECTURE.md — System Design & Patterns

## System Overview

TradingAgents is a **multi-agent LLM framework** for automated financial trading analysis. It uses a **directed acyclic graph (DAG) of specialized LLM agents** that collectively analyze a stock and produce a trade decision (BUY / SELL / HOLD + rationale).

The framework is centered on **LangGraph** — a stateful graph execution engine — with LangChain for LLM abstractions.

## High-Level Data Flow

```
User Input (ticker, date)
        │
        ▼
  TradingAgentsGraph.propagate()
        │
        ▼
  ┌─────────────────────────────────────┐
  │           Analyst Layer             │
  │  Market → Social → News → Fundam.  │  ← runs in sequence (configurable subset)
  │  (each uses tool calls to fetch    │
  │   financial data from yfinance /   │
  │   Alpha Vantage)                   │
  └───────────────┬─────────────────────┘
                  │ Reports aggregated in AgentState
                  ▼
  ┌─────────────────────────────────────┐
  │        Research Debate Layer        │
  │  Bull Researcher ↔ Bear Researcher  │  ← debate up to max_debate_rounds
  │  → Research Manager (judge)         │  ← deep LLM makes investment decision
  └───────────────┬─────────────────────┘
                  │
                  ▼
  ┌─────────────────────────────────────┐
  │           Trader Layer              │
  │  Trader creates investment plan     │
  └───────────────┬─────────────────────┘
                  │
                  ▼
  ┌─────────────────────────────────────┐
  │        Risk Debate Layer            │
  │  Aggressive ↔ Conservative ↔ Neutral│  ← debate up to max_risk_discuss_rounds
  │  → Portfolio Manager (judge)        │  ← deep LLM makes final decision
  └───────────────┬─────────────────────┘
                  │
                  ▼
            Final Trade Decision
            (logged to JSON file)
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
TradingAgentsGraph (orchestrator)
├── GraphSetup       — builds and compiles the StateGraph
├── Propagator       — creates initial state, runs graph
├── Reflector        — post-trade reflection, updates agent memories
├── SignalProcessor  — parses final_trade_decision string → clean signal
└── ConditionalLogic — edge routing functions
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
