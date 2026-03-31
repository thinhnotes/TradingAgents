---
wave: 2
depends_on: [01]
files_modified:
  - cli/main.py
requirements_addressed: [MKTC-03]
autonomous: true
---

# Plan 04: CLI Market Selection

<objective>
Add a market selection step to the CLI interactive flow so users can choose between US and VN markets before entering a ticker. The market choice flows into the config used by TradingAgentsGraph.
</objective>

<must_haves>
- CLI presents market selection (US / VN) as a new step
- Selected market is stored in config passed to TradingAgentsGraph
- Default market comes from TRADINGAGENTS_DEFAULT_MARKET env var (or "US")
- Ticker prompt text adjusts based on selected market
- Backward compatible — if env says "US", US is pre-selected
</must_haves>

## Tasks

### Task 1: Add market selection function and step to CLI

<read_first>
- cli/main.py (lines 462-611, the get_user_selections function)
- tradingagents/dataflows/market_config.py
</read_first>

<action>
In `cli/main.py`, make these changes:

1. Add import near the top of the file (with other imports):
```python
from tradingagents.dataflows.market_config import SUPPORTED_MARKETS, get_market_metadata
```

2. Add a new function `ask_market()` before the `get_user_selections()` function:
```python
def ask_market():
    """Ask user to select market."""
    default_market = os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US")
    choices = [
        questionary.Choice(
            title=f"US — {get_market_metadata('US')['exchange']} ({get_market_metadata('US')['currency']})",
            value="US",
        ),
        questionary.Choice(
            title=f"VN — {get_market_metadata('VN')['exchange']} ({get_market_metadata('VN')['currency']})",
            value="VN",
        ),
    ]
    # Move default to front
    if default_market == "VN":
        choices = choices[::-1]
    
    return questionary.select(
        "Select market:",
        choices=choices,
    ).ask()
```

3. In `get_user_selections()`, add a new "Step 0: Market" BEFORE the existing "Step 1: Ticker Symbol". Insert this code right after `console.print()  # Add vertical space before announcements` and `display_announcements(console, announcements)`:

```python
    # Step 0: Market
    console.print(
        create_question_box(
            "Step 0: Market",
            "Select the market to analyze",
            os.getenv("TRADINGAGENTS_DEFAULT_MARKET", "US"),
        )
    )
    selected_market = ask_market()
    console.print(f"[green]Selected market:[/green] {selected_market}")
```

4. Update the "Step 1: Ticker Symbol" prompt text to be market-aware. Change the `create_question_box` call for ticker to:
```python
    ticker_prompt = (
        "Enter the HOSE ticker symbol (e.g., FPT, VNM, VIC, HPG, SSI)"
        if selected_market == "VN"
        else "Enter the exact ticker symbol to analyze, including exchange suffix when needed (examples: SPY, CNC.TO, 7203.T, 0700.HK)"
    )
    ticker_default = "FPT" if selected_market == "VN" else "SPY"
    console.print(
        create_question_box(
            "Step 1: Ticker Symbol",
            ticker_prompt,
            ticker_default,
        )
    )
    selected_ticker = get_ticker(default=ticker_default)
```

5. Update `get_ticker()` to accept a default parameter:
```python
def get_ticker(default="SPY"):
    """Get ticker symbol from user input."""
    return typer.prompt("", default=default)
```

6. Add `"market": selected_market` to the return dict of `get_user_selections()`:
```python
    return {
        "market": selected_market,
        "ticker": selected_ticker,
        ...
    }
```

7. In `run_analysis()`, add market to config after `config = DEFAULT_CONFIG.copy()`:
```python
    config["market"] = selections["market"]
```
</action>

<acceptance_criteria>
- `cli/main.py` contains `from tradingagents.dataflows.market_config import SUPPORTED_MARKETS, get_market_metadata`
- `cli/main.py` contains `def ask_market()` function
- `get_user_selections()` includes "Step 0: Market" question box
- `get_user_selections()` return dict includes `"market"` key
- `run_analysis()` sets `config["market"]` from selections
- `get_ticker()` accepts `default` parameter
- Ticker prompt shows VN examples when market is "VN"
</acceptance_criteria>

## Verification

```bash
grep -n "ask_market\|selected_market\|Step 0: Market" cli/main.py | head -20
grep -n "\"market\":" cli/main.py | head -10
```

---
*Phase: 01-market-configuration-detection*
