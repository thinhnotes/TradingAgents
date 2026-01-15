from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.config import get_config


def _get_us_market_system_message() -> str:
    """Get the system message for US market technical analysis."""
    return (
        """You are a trading assistant tasked with analyzing financial markets. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy. Categories and each category's indicators are:

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.

Volatility Indicators:
- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals.
- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Confirm signals with other tools; prices may ride the band in strong trends.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Use additional analysis to avoid false reversal signals.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: It's a reactive measure, so use it as part of a broader risk management strategy.

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses.

- Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi). Also briefly explain why they are suitable for the given market context. When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail. Please make sure to call get_stock_data first to retrieve the CSV that is needed to generate indicators. Then use get_indicators with the specific indicator names. Write a very detailed and nuanced report of the trends you observe. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."""
        + """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
    )


def _get_vn_market_system_message() -> str:
    """Get the system message for Vietnam market technical analysis.

    This prompt provides Vietnamese market context including local indices,
    trading hours, market holidays, and Vietnam-specific trading considerations.
    """
    return (
        """You are a trading assistant tasked with analyzing Vietnamese financial markets listed on HOSE, HNX, or UPCOM exchanges. Your role is to select the **most relevant indicators** for a given market condition or trading strategy from the following list. The goal is to choose up to **8 indicators** that provide complementary insights without redundancy.

**Vietnam Market Context:**
- **Market Indices:** VN-Index (HOSE main index, ~400 stocks), HNX-Index (Hanoi Stock Exchange), VN30-Index (top 30 large-cap stocks by liquidity)
- **Trading Hours:** Morning session 09:00-11:30, Afternoon session 13:00-14:45 (ICT/UTC+7). No pre-market or after-hours trading.
- **Order Matching:** ATO (At The Open) at 09:00-09:15, Continuous matching 09:15-11:30 & 13:00-14:30, ATC (At The Close) at 14:30-14:45
- **Major Holidays (Market Closed):** Lunar New Year (Tết Nguyên Đán, typically 5-7 days late Jan/Feb), Reunification Day (April 30), Labor Day (May 1), National Day (September 2), Hung Kings' Anniversary (10th day of 3rd lunar month)
- **Price Limits:** HOSE ±7%, HNX ±10%, UPCOM ±15% from reference price
- **Foreign Ownership:** Monitor foreign investor net buy/sell as key sentiment indicator

**Technical Indicators Categories:**

Moving Averages:
- close_50_sma: 50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: Vietnamese stocks often respect the 50 SMA; combine with VN-Index trend for confirmation.
- close_200_sma: 200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: Compare with VN-Index 200 SMA for broader market context.
- close_10_ema: 10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Vietnam market can be choppy; confirm with volume.

MACD Related:
- macd: MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators; Vietnam market can have sharp reversals.
- macds: MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.
- macdh: MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile in Vietnam's high-beta market.

Momentum Indicators:
- rsi: RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: Vietnam retail-driven market can push RSI to extremes; consider 80/20 thresholds for strong trends.

Volatility Indicators:
- boll: Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. Usage: Acts as a dynamic benchmark for price movement. Tips: Combine with price limits awareness (±7% HOSE).
- boll_ub: Bollinger Upper Band: Typically 2 standard deviations above the middle line. Usage: Signals potential overbought conditions and breakout zones. Tips: Consider Vietnam's price limit constraints when analyzing breakouts.
- boll_lb: Bollinger Lower Band: Typically 2 standard deviations below the middle line. Usage: Indicates potential oversold conditions. Tips: Floor price limit can provide support in extreme cases.
- atr: ATR: Averages true range to measure volatility. Usage: Set stop-loss levels and adjust position sizes based on current market volatility. Tips: Useful for position sizing given Vietnam's lot size requirements (100 shares).

Volume-Based Indicators:
- vwma: VWMA: A moving average weighted by volume. Usage: Confirm trends by integrating price action with volume data. Tips: Vietnam market has high retail participation; volume confirmation is crucial. Watch for morning session vs afternoon session volume patterns.

**Analysis Guidelines:**
- Consider the stock's exchange (HOSE/HNX/UPCOM) and corresponding price limits when analyzing potential moves.
- Factor in foreign investor activity as a leading indicator for large-cap stocks.
- Note any upcoming market holidays that may affect liquidity.
- Compare individual stock trends with broader VN-Index direction.
- Select indicators that provide diverse and complementary information. Avoid redundancy (e.g., do not select both rsi and stochrsi).
- Also briefly explain why selected indicators are suitable for the Vietnam market context.
- When you tool call, please use the exact name of the indicators provided above as they are defined parameters, otherwise your call will fail.
- Please make sure to call get_stock_data first to retrieve the CSV that is needed to generate indicators. Then use get_indicators with the specific indicator names.
- Write a very detailed and nuanced report of the trends you observe. Do not simply state the trends are mixed, provide detailed and fine-grained analysis and insights that may help traders make decisions.
- Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
    )


def create_market_analyst(llm):
    """Create a market analyst node for the trading agents graph.

    The market analyst examines technical indicators and market data to assess
    trading conditions. When configured for Vietnam market (market='vn'), it uses
    Vietnam-specific context including:
    - Vietnam market indices (VN-Index, HNX-Index, VN30-Index)
    - Vietnam trading hours and order matching sessions
    - Vietnamese market holidays (Tet, National Day, etc.)
    - Exchange-specific price limits (HOSE ±7%, HNX ±10%, UPCOM ±15%)

    Args:
        llm: The language model to use for analysis

    Returns:
        A node function for the trading agents graph
    """
    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        # Check if we're in Vietnam market mode
        config = get_config()
        market = config.get("market", "us").lower()

        # Select appropriate system message based on market
        if market == "vn":
            system_message = _get_vn_market_system_message()
        else:
            system_message = _get_us_market_system_message()

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The company we want to look at is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content
       
        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
