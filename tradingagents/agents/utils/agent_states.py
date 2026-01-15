from typing import Annotated, Sequence, Dict, List
from datetime import date, timedelta, datetime
from typing_extensions import TypedDict, Optional
from langchain_openai import ChatOpenAI
from tradingagents.agents import *
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, START, MessagesState


# ============================================================================
# Vietnam Market Holdings Tracking (T+2.5 Settlement)
# ============================================================================


class VNHolding(TypedDict):
    """
    Represents a single stock holding with purchase tracking for T+2.5 settlement.

    In the Vietnam stock market, stocks purchased on day T can only be sold
    from the morning of T+3 (2.5 business days settlement period).
    """
    ticker: Annotated[str, "Stock ticker symbol (e.g., VNM, FPT, TCB)"]
    quantity: Annotated[int, "Number of shares held"]
    purchase_date: Annotated[str, "Date of purchase in YYYY-MM-DD format"]
    purchase_price: Annotated[Optional[float], "Price per share at purchase (VND)"]
    exchange: Annotated[str, "Exchange code: HOSE, HNX, or UPCOM"]


def create_vn_holding(
    ticker: str,
    quantity: int,
    purchase_date: str,
    purchase_price: float = None,
    exchange: str = "HOSE"
) -> VNHolding:
    """
    Create a new VNHolding record.

    Args:
        ticker: Stock ticker symbol
        quantity: Number of shares
        purchase_date: Date of purchase (YYYY-MM-DD format)
        purchase_price: Optional price per share at purchase
        exchange: Exchange code (defaults to HOSE)

    Returns:
        VNHolding dictionary
    """
    return VNHolding(
        ticker=ticker.upper().strip(),
        quantity=quantity,
        purchase_date=purchase_date,
        purchase_price=purchase_price,
        exchange=exchange.upper().strip()
    )


def can_sell_holding(holding: VNHolding, sell_date: str = None) -> tuple:
    """
    Check if a holding can be sold based on T+2.5 settlement rule.

    In Vietnam, stocks can only be sold from the morning of T+3 (where T is
    the purchase date).

    Args:
        holding: VNHolding to check
        sell_date: Date to sell (YYYY-MM-DD). Defaults to today.

    Returns:
        Tuple of (can_sell: bool, earliest_sell_date: str, message: str)

    Example:
        >>> holding = create_vn_holding("VNM", 100, "2024-01-15")
        >>> can_sell, earliest, msg = can_sell_holding(holding, "2024-01-17")
        >>> print(can_sell)
        False
        >>> print(earliest)
        2024-01-18
    """
    # Parse purchase date
    try:
        purchase_dt = datetime.strptime(holding["purchase_date"], "%Y-%m-%d")
    except (ValueError, KeyError):
        return False, None, f"Invalid purchase date format: {holding.get('purchase_date')}"

    # Parse sell date (default to today)
    if sell_date is None:
        sell_dt = datetime.now()
        sell_date = sell_dt.strftime("%Y-%m-%d")
    else:
        try:
            sell_dt = datetime.strptime(sell_date, "%Y-%m-%d")
        except ValueError:
            return False, None, f"Invalid sell date format: {sell_date}"

    # Calculate earliest sell date (T+3 for T+2.5 rule)
    earliest_sell_dt = purchase_dt + timedelta(days=3)
    earliest_sell_date = earliest_sell_dt.strftime("%Y-%m-%d")

    # Check if we can sell
    if sell_dt >= earliest_sell_dt:
        return True, earliest_sell_date, f"Can sell {holding['ticker']}: Settlement period complete"
    else:
        days_remaining = (earliest_sell_dt - sell_dt).days
        return (
            False,
            earliest_sell_date,
            f"Cannot sell {holding['ticker']}: T+2.5 settlement not complete. "
            f"Purchased on {holding['purchase_date']}, can sell from {earliest_sell_date} "
            f"({days_remaining} day(s) remaining)"
        )


def get_sellable_holdings(
    holdings: List[VNHolding],
    sell_date: str = None
) -> tuple:
    """
    Filter holdings to find which can be sold based on T+2.5 settlement.

    Args:
        holdings: List of VNHolding records
        sell_date: Date to check for selling (YYYY-MM-DD). Defaults to today.

    Returns:
        Tuple of (sellable: List[VNHolding], unsellable: List[dict])
        where unsellable items include the holding and reason.
    """
    sellable = []
    unsellable = []

    for holding in holdings:
        can_sell, earliest_date, message = can_sell_holding(holding, sell_date)
        if can_sell:
            sellable.append(holding)
        else:
            unsellable.append({
                "holding": holding,
                "earliest_sell_date": earliest_date,
                "message": message
            })

    return sellable, unsellable


def get_holdings_for_ticker(
    holdings: List[VNHolding],
    ticker: str
) -> List[VNHolding]:
    """
    Get all holdings for a specific ticker.

    Args:
        holdings: List of VNHolding records
        ticker: Stock ticker to filter by

    Returns:
        List of VNHolding records for the ticker
    """
    ticker_upper = ticker.upper().strip()
    return [h for h in holdings if h["ticker"] == ticker_upper]


def get_holdings_summary(
    holdings: List[VNHolding],
    current_date: str = None
) -> str:
    """
    Generate a summary of holdings with settlement status.

    Args:
        holdings: List of VNHolding records
        current_date: Current date for settlement check (YYYY-MM-DD)

    Returns:
        Formatted string summary of holdings
    """
    if not holdings:
        return "No holdings in portfolio."

    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")

    lines = ["## Vietnam Market Holdings", ""]

    # Group by ticker
    ticker_holdings: Dict[str, List[VNHolding]] = {}
    for h in holdings:
        ticker = h["ticker"]
        if ticker not in ticker_holdings:
            ticker_holdings[ticker] = []
        ticker_holdings[ticker].append(h)

    for ticker, ticker_list in sorted(ticker_holdings.items()):
        total_qty = sum(h["quantity"] for h in ticker_list)
        lines.append(f"### {ticker} ({total_qty} shares total)")

        for h in ticker_list:
            can_sell, earliest_date, _ = can_sell_holding(h, current_date)
            status = "✓ Sellable" if can_sell else f"⏳ Locked until {earliest_date}"
            price_str = f" @ {h['purchase_price']:,.0f} VND" if h.get("purchase_price") else ""
            lines.append(
                f"- {h['quantity']} shares purchased {h['purchase_date']}{price_str} "
                f"[{h['exchange']}] - {status}"
            )

        lines.append("")

    return "\n".join(lines)


# Researcher team state
class InvestDebateState(TypedDict):
    bull_history: Annotated[
        str, "Bullish Conversation history"
    ]  # Bullish Conversation history
    bear_history: Annotated[
        str, "Bearish Conversation history"
    ]  # Bullish Conversation history
    history: Annotated[str, "Conversation history"]  # Conversation history
    current_response: Annotated[str, "Latest response"]  # Last response
    judge_decision: Annotated[str, "Final judge decision"]  # Last response
    count: Annotated[int, "Length of the current conversation"]  # Conversation length


# Risk management team state
class RiskDebateState(TypedDict):
    risky_history: Annotated[
        str, "Risky Agent's Conversation history"
    ]  # Conversation history
    safe_history: Annotated[
        str, "Safe Agent's Conversation history"
    ]  # Conversation history
    neutral_history: Annotated[
        str, "Neutral Agent's Conversation history"
    ]  # Conversation history
    history: Annotated[str, "Conversation history"]  # Conversation history
    latest_speaker: Annotated[str, "Analyst that spoke last"]
    current_risky_response: Annotated[
        str, "Latest response by the risky analyst"
    ]  # Last response
    current_safe_response: Annotated[
        str, "Latest response by the safe analyst"
    ]  # Last response
    current_neutral_response: Annotated[
        str, "Latest response by the neutral analyst"
    ]  # Last response
    judge_decision: Annotated[str, "Judge's decision"]
    count: Annotated[int, "Length of the current conversation"]  # Conversation length


class AgentState(MessagesState):
    company_of_interest: Annotated[str, "Company that we are interested in trading"]
    trade_date: Annotated[str, "What date we are trading at"]

    sender: Annotated[str, "Agent that sent this message"]

    # research step
    market_report: Annotated[str, "Report from the Market Analyst"]
    sentiment_report: Annotated[str, "Report from the Social Media Analyst"]
    news_report: Annotated[
        str, "Report from the News Researcher of current world affairs"
    ]
    fundamentals_report: Annotated[str, "Report from the Fundamentals Researcher"]

    # researcher team discussion step
    investment_debate_state: Annotated[
        InvestDebateState, "Current state of the debate on if to invest or not"
    ]
    investment_plan: Annotated[str, "Plan generated by the Analyst"]

    trader_investment_plan: Annotated[str, "Plan generated by the Trader"]

    # risk management team discussion step
    risk_debate_state: Annotated[
        RiskDebateState, "Current state of the debate on evaluating risk"
    ]
    final_trade_decision: Annotated[str, "Final decision made by the Risk Analysts"]

    # Vietnam market holdings tracking (T+2.5 settlement)
    # List of VNHolding records tracking purchase dates for settlement validation
    vn_holdings: Annotated[
        List[VNHolding],
        "Vietnam stock holdings with purchase dates for T+2.5 settlement tracking"
    ]
