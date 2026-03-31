---
wave: 1
depends_on: []
files_modified:
  - tradingagents/agents/utils/agent_states.py
  - tradingagents/graph/propagation.py
requirements_addressed: [MKTC-04, MKTC-05]
autonomous: true
---

# Plan 02: Market-Aware Agent State & Propagation

<objective>
Extend `AgentState` with market context fields and update `Propagator` to populate them from config. This ensures every agent in the graph has access to market, currency, and exchange metadata without changing any existing agent logic.
</objective>

<must_haves>
- AgentState includes market, market_metadata fields
- Propagator populates market context from config
- Existing state fields unchanged
- Backward compatible — market defaults to "US" if not in config
</must_haves>

## Tasks

### Task 1: Add market fields to AgentState

<read_first>
- tradingagents/agents/utils/agent_states.py
</read_first>

<action>
In `tradingagents/agents/utils/agent_states.py`, add these fields to the `AgentState` class at the end (after `final_trade_decision`):

```python
    # market context
    market: Annotated[str, "Market code (US or VN)"]
    market_metadata: Annotated[dict, "Market metadata (currency, exchange, trading hours)"]
```

No imports needed — `Annotated` and `dict` already available.
</action>

<acceptance_criteria>
- `agent_states.py` contains `market: Annotated[str, "Market code (US or VN)"]`
- `agent_states.py` contains `market_metadata: Annotated[dict, "Market metadata`
- `AgentState` class has fields `market` and `market_metadata`
</acceptance_criteria>

### Task 2: Update Propagator to include market context in initial state

<read_first>
- tradingagents/graph/propagation.py
- tradingagents/dataflows/market_config.py
- tradingagents/dataflows/config.py
</read_first>

<action>
In `tradingagents/graph/propagation.py`:

1. Add import at the top (after existing imports):
```python
from tradingagents.dataflows.market_config import get_market_metadata
from tradingagents.dataflows.config import get_config
```

2. In `create_initial_state()` method, add market context to the returned dict. After the `"news_report": ""` line, add:
```python
            # Market context
            "market": get_config().get("market", "US"),
            "market_metadata": get_market_metadata(get_config().get("market", "US")),
```
</action>

<acceptance_criteria>
- `propagation.py` contains `from tradingagents.dataflows.market_config import get_market_metadata`
- `propagation.py` contains `"market": get_config().get("market", "US")`
- `propagation.py` contains `"market_metadata": get_market_metadata(`
- Initial state dict includes `market` and `market_metadata` keys
</acceptance_criteria>

## Verification

```bash
python -c "
from tradingagents.graph.propagation import Propagator
p = Propagator()
state = p.create_initial_state('AAPL', '2024-01-01')
assert 'market' in state, 'market not in state'
assert 'market_metadata' in state, 'market_metadata not in state'
assert state['market'] == 'US', f'Expected US, got {state[\"market\"]}'
assert state['market_metadata']['currency'] == 'USD'
print('✓ State includes market context')
"
```

---
*Phase: 01-market-configuration-detection*
