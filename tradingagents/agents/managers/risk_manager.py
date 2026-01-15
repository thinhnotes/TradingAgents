import time
import json
from typing import Optional

from tradingagents.dataflows.config import get_config


def create_risk_manager(llm, memory):
    """Create a risk manager node for the trading agents graph.

    The risk manager evaluates debates between risk analysts (Risky, Neutral, Safe)
    and makes a final recommendation. When configured for Vietnam market (market='vn'),
    it applies Vietnam-specific trading rules including:
    - T+2.5 settlement rule
    - Lot size requirements (multiples of 100)
    - Exchange-specific price limits (HOSE ±7%, HNX ±10%, UPCOM ±15%)

    Args:
        llm: The language model to use for generating decisions
        memory: Memory object for retrieving past recommendations

    Returns:
        A node function for the trading agents graph
    """
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["news_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        # Check if we're in Vietnam market mode
        config = get_config()
        market = config.get("market", "us").lower()

        # Build Vietnam market rules context if applicable
        vn_market_rules_context = ""
        if market == "vn":
            # Import VNMarketRules only when needed (lazy import)
            from tradingagents.rules import VNMarketRules

            vn_rules = VNMarketRules()
            vn_market_rules_context = _get_vn_market_rules_context(
                vn_rules, company_name
            )

        # Build the base prompt
        base_prompt = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe/Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money."""

        # Add Vietnam market rules section if applicable
        if vn_market_rules_context:
            base_prompt += f"""

---

**IMPORTANT: Vietnam Market Trading Rules**

{vn_market_rules_context}

When making your recommendation, you MUST:
1. Ensure any SELL recommendation accounts for T+2.5 settlement (stocks cannot be sold until 3 days after purchase)
2. Ensure any order quantities are rounded down to multiples of 100 shares
3. Be aware of exchange-specific daily price limits when evaluating price targets
4. If a trade would violate these rules, clearly state the violation and adjust your recommendation accordingly"""

        # Complete the prompt
        prompt = base_prompt + f"""

Deliverables:
- A clear and actionable recommendation: Buy, Sell, or Hold.
- Detailed reasoning anchored in the debate and past reflections."""

        if market == "vn":
            prompt += """
- For Vietnam market: Confirm that the recommendation complies with all Vietnam trading rules (T+2.5, lot size, price limits)."""

        prompt += f"""

---

**Analysts Debate History:**
{history}

---

Focus on actionable insights and continuous improvement. Build on past lessons, critically evaluate all perspectives, and ensure each decision advances better outcomes."""

        response = llm.invoke(prompt)

        # Post-process response for Vietnam market compliance
        final_decision = response.content
        if market == "vn":
            final_decision = _add_vn_compliance_note(
                response.content, company_name
            )

        new_risk_debate_state = {
            "judge_decision": final_decision,
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": final_decision,
        }

    return risk_manager_node


def _get_vn_market_rules_context(vn_rules, ticker: str) -> str:
    """Generate Vietnam market rules context for the risk manager prompt.

    Args:
        vn_rules: VNMarketRules instance
        ticker: Stock ticker symbol

    Returns:
        Formatted string with Vietnam market rules context
    """
    exchange = vn_rules.get_exchange(ticker)
    exchange_info = vn_rules.get_exchange_info(exchange)

    context = f"""**Trading Rules for {ticker} on {exchange} ({exchange_info['name']})**

1. **Settlement Rule (T+2.5)**:
   - Stocks purchased today can only be sold from the morning of T+3 (2.5 business days later)
   - If recommending SELL, verify the stock has been held for at least 3 days
   - Violation will result in: "Cannot sell - stock not yet settled"

2. **Lot Size Requirement**:
   - All orders must be in multiples of 100 shares
   - If recommending a specific quantity, round DOWN to nearest 100
   - Example: 150 shares → 100 shares; 50 shares → cannot trade (below minimum)

3. **Daily Price Limits for {exchange}**:
   - Maximum daily price movement: ±{exchange_info['price_limit_percent']}% from reference price
   - Floor price = Reference price × {1 - exchange_info['price_limit_percent']/100:.2f}
   - Ceiling price = Reference price × {1 + exchange_info['price_limit_percent']/100:.2f}
   - Orders outside these limits will be rejected

4. **Trading Hours**: {exchange_info['trading_hours']} ({exchange_info['timezone']})

5. **Currency**: Vietnamese Dong (VND) - no fractional shares allowed"""

    return context


def _add_vn_compliance_note(decision_content: str, ticker: str) -> str:
    """Add Vietnam market compliance note to the decision if not already present.

    This function ensures the final decision includes a note about Vietnam market
    rules compliance for transparency.

    Args:
        decision_content: The LLM's decision content
        ticker: Stock ticker symbol

    Returns:
        Decision content with compliance note appended if needed
    """
    # Check if the decision already mentions Vietnam rules
    vn_keywords = [
        "T+2.5", "t+2.5",
        "lot size", "multiples of 100",
        "price limit", "HOSE", "HNX", "UPCOM",
        "Vietnam market", "VN market"
    ]

    has_vn_mention = any(keyword.lower() in decision_content.lower() for keyword in vn_keywords)

    if not has_vn_mention:
        # Add a compliance note
        compliance_note = f"""

---
**Vietnam Market Compliance Note for {ticker}:**
This recommendation is subject to Vietnam stock market trading rules:
- T+2.5 settlement applies (3-day holding period before selling)
- Order quantities must be in multiples of 100 shares
- Daily price limits apply based on the exchange (HOSE ±7%, HNX ±10%, UPCOM ±15%)
"""
        return decision_content + compliance_note

    return decision_content
