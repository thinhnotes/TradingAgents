from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_news, get_global_news
from tradingagents.dataflows.config import get_config


def _get_us_news_system_message() -> str:
    """Get the system message for US market news analysis."""
    return (
        "You are a news researcher tasked with analyzing recent news and trends over the past week. Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. Use the available tools: get_news(query, start_date, end_date) for company-specific or targeted news searches, and get_global_news(curr_date, look_back_days, limit) for broader macroeconomic news. Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
        " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
    )


def _get_vn_news_system_message() -> str:
    """Get the system message for Vietnam market news analysis.

    This prompt provides Vietnamese market context including local news sources,
    economic context, and Vietnam-specific trading considerations.
    """
    return (
        "You are a news researcher tasked with analyzing recent news and trends from the Vietnamese stock market "
        "over the past week. Please write a comprehensive report of the current state of the Vietnamese market "
        "that is relevant for trading stocks listed on HOSE, HNX, or UPCOM exchanges.\n\n"

        "**Vietnamese News Sources:**\n"
        "The news data comes from major Vietnamese financial news portals:\n"
        "- **CafeF (cafef.vn):** One of Vietnam's largest financial news portals, comprehensive coverage of stock market, business, and economic news\n"
        "- **Vietstock (vietstock.vn):** Specialized financial data and news portal with detailed company analysis\n"
        "- **VnExpress Business (vnexpress.net/kinh-doanh):** Business section of Vietnam's largest online newspaper, covers macroeconomic news and corporate developments\n\n"

        "**Vietnam Economic Context to Consider:**\n"
        "- **VN-Index Performance:** Track the main HOSE index performance and trends\n"
        "- **Foreign Investor Activity (Khối ngoại):** Foreign net buy/sell is a key market sentiment indicator\n"
        "- **Interest Rates:** State Bank of Vietnam (SBV) policy rates affect market liquidity and banking stocks\n"
        "- **Real Estate Sector (Bất động sản):** Major sector in VN market, sensitive to regulations and interest rates\n"
        "- **Banking Sector (Ngân hàng):** High market weight, watch for credit growth and NPL developments\n"
        "- **FDI News:** Foreign direct investment inflows affect manufacturing and export sectors\n"
        "- **Exchange Rate (USD/VND):** Currency stability affects market sentiment and export companies\n\n"

        "**Key Vietnam Market Events to Watch:**\n"
        "- State Bank of Vietnam policy announcements\n"
        "- Government regulations affecting real estate, banking, or securities sectors\n"
        "- Corporate earnings announcements (quarterly and annual reports)\n"
        "- Foreign ownership limit changes for specific stocks\n"
        "- Major IPOs or listings on HOSE, HNX, or UPCOM\n\n"

        "**Analysis Guidelines:**\n"
        "Use the available tools: get_news(query, start_date, end_date) for company-specific or targeted news searches, "
        "and get_global_news(curr_date, look_back_days, limit) for broader Vietnamese market and economic news.\n\n"
        "Do not simply state the trends are mixed - provide detailed and fine-grained analysis and insights "
        "that may help traders make decisions in the Vietnamese market context.\n\n"
        "Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
    )


def create_news_analyst(llm):
    """Create a news analyst node for the trading agents graph.

    The news analyst examines recent news and market trends to inform trading decisions.
    When configured for Vietnam market (market='vn'), it uses Vietnam-specific context including:
    - Vietnamese news sources (CafeF, Vietstock, VnExpress)
    - Vietnam economic context (VN-Index, foreign investor activity, SBV policy)
    - Vietnam-specific sectors (banking, real estate)
    - Key Vietnam market events to watch

    Args:
        llm: The language model to use for analysis

    Returns:
        A node function for the trading agents graph
    """
    def news_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        tools = [
            get_news,
            get_global_news,
        ]

        # Check if we're in Vietnam market mode
        config = get_config()
        market = config.get("market", "us").lower()

        # Select appropriate system message based on market
        if market == "vn":
            system_message = _get_vn_news_system_message()
        else:
            system_message = _get_us_news_system_message()

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
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
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
            "news_report": report,
        }

    return news_analyst_node
