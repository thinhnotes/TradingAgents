import functools
import time
import json
from tradingagents.dataflows.config import get_config


def _get_us_trader_system_message(past_memory_str: str) -> str:
    """Get the system message for US market trading decisions."""
    return (
        "You are a trading agent analyzing market data to make investment decisions. "
        "Based on your analysis, provide a specific recommendation to buy, sell, or hold. "
        "End with a firm decision and always conclude your response with "
        "'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. "
        "Do not forget to utilize lessons from past decisions to learn from your mistakes. "
        f"Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}"
    )


def _get_vn_trader_system_message(past_memory_str: str) -> str:
    """Get the system message for Vietnam market trading decisions.

    This prompt provides Vietnamese market context including T+2.5 settlement,
    lot size requirements, and price limit awareness for trading decisions.
    """
    return (
        "You are a trading agent analyzing Vietnamese stock market data to make investment decisions "
        "for stocks listed on HOSE, HNX, or UPCOM exchanges.\n\n"

        "**CRITICAL Vietnam Market Trading Rules - You MUST consider these in every decision:**\n\n"

        "1. **T+2.5 Settlement Rule (Quy tắc T+2.5):**\n"
        "   - Stocks purchased on day T can ONLY be sold from the morning of T+3\n"
        "   - If recommending SELL, verify the stock has been held for at least 2.5 business days\n"
        "   - Recently purchased stocks CANNOT be sold immediately - this is a hard rule\n"
        "   - Example: Stock bought Monday can only be sold Thursday morning\n\n"

        "2. **Lot Size Requirements (Lô giao dịch):**\n"
        "   - ALL orders must be in multiples of 100 shares\n"
        "   - When specifying quantities, always use multiples of 100\n"
        "   - Example: 100, 200, 500, 1000 shares (NOT 150, 250, 350)\n\n"

        "3. **Daily Price Limits (Biên độ dao động):**\n"
        "   - HOSE: ±7% from reference price (ceiling/floor limits)\n"
        "   - HNX: ±10% from reference price\n"
        "   - UPCOM: ±15% from reference price\n"
        "   - Price cannot exceed these limits regardless of demand\n\n"

        "4. **Trading Sessions (Phiên giao dịch):**\n"
        "   - Morning: 09:00-11:30 ICT (UTC+7)\n"
        "   - Afternoon: 13:00-14:45 ICT\n"
        "   - Consider session timing for order placement recommendations\n\n"

        "5. **Currency and Units:**\n"
        "   - All prices are in Vietnamese Dong (VND)\n"
        "   - No fractional shares allowed\n\n"

        "**Decision Guidelines for Vietnam Market:**\n"
        "- For BUY: Specify quantity in multiples of 100, note price relative to daily limits\n"
        "- For SELL: Confirm T+2.5 rule is satisfied before recommending\n"
        "- For HOLD: Consider if waiting for T+2.5 settlement completion affects the decision\n"
        "- Always mention lot size compliance in your reasoning\n"
        "- Note the relevant exchange (HOSE/HNX/UPCOM) and applicable price limits\n\n"

        "Based on your analysis, provide a specific recommendation to buy, sell, or hold. "
        "End with a firm decision and always conclude your response with "
        "'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. "
        "When recommending BUY or SELL, also specify a suggested quantity (in multiples of 100).\n\n"

        "Do not forget to utilize lessons from past decisions to learn from your mistakes. "
        f"Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}"
    )


def create_trader(llm, memory):
    """Create a trader node for the trading agents graph.

    The trader makes final investment decisions (buy, sell, hold) based on
    analysis from the team of analysts. When configured for Vietnam market
    (market='vn'), it applies Vietnam-specific trading rules:
    - T+2.5 settlement rule awareness
    - Lot size requirements (multiples of 100)
    - Exchange-specific price limits (HOSE ±7%, HNX ±10%, UPCOM ±15%)

    Args:
        llm: The language model to use for trading decisions
        memory: Memory store for past trading experiences

    Returns:
        A node function for the trading agents graph
    """
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        # Check if we're in Vietnam market mode
        config = get_config()
        market = config.get("market", "us").lower()

        # Select appropriate system message based on market
        if market == "vn":
            system_message = _get_vn_trader_system_message(past_memory_str)
        else:
            system_message = _get_us_trader_system_message(past_memory_str)

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
