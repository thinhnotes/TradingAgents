from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time
import json
from tradingagents.agents.utils.agent_utils import get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement, get_insider_sentiment, get_insider_transactions
from tradingagents.dataflows.config import get_config


def _get_us_fundamentals_system_message() -> str:
    """Get the system message for US market fundamentals analysis."""
    return (
        "You are a researcher tasked with analyzing fundamental information over the past week about a company. "
        "Please write a comprehensive report of the company's fundamental information such as financial documents, "
        "company profile, basic company financials, and company financial history to gain a full view of the company's "
        "fundamental information to inform traders. Make sure to include as much detail as possible. Do not simply state "
        "the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
        " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
        " Use the available tools: `get_fundamentals` for comprehensive company analysis, `get_balance_sheet`, `get_cashflow`, and `get_income_statement` for specific financial statements."
    )


def _get_vn_fundamentals_system_message() -> str:
    """Get the system message for Vietnam market fundamentals analysis.

    This prompt is in English but provides Vietnamese financial context to help
    the LLM understand Vietnam-specific accounting practices and market structure.
    """
    return (
        "You are a researcher tasked with analyzing fundamental information about a Vietnamese company listed on "
        "HOSE, HNX, or UPCOM stock exchanges. Please write a comprehensive report analyzing the company's "
        "financial health based on Vietnamese accounting standards (VAS) and financial disclosures.\n\n"

        "**Key Financial Documents to Analyze (Vietnamese Market Context):**\n"
        "- Consolidated Financial Statements (Báo cáo tài chính hợp nhất): The primary financial disclosure for Vietnamese companies, "
        "equivalent to 10-K filings in the US. Pay special attention to:\n"
        "  - Accounts Receivable (Các khoản phải thu): High receivables may indicate collection issues\n"
        "  - Bank Loans & Debt (Nợ vay ngân hàng): Vietnam companies often have high leverage\n"
        "  - Related Party Transactions: Common in Vietnamese conglomerates\n"
        "- Balance Sheet (Bảng cân đối kế toán)\n"
        "- Cash Flow Statement (Báo cáo lưu chuyển tiền tệ)\n"
        "- Income Statement (Báo cáo kết quả kinh doanh)\n\n"

        "**Vietnam-Specific Sectors to Consider:**\n"
        "- Banking (Ngân hàng): Major sector in Vietnam, watch for NPL ratios and credit growth\n"
        "- Real Estate (Bất động sản): High market weight, sensitive to interest rates and regulations\n"
        "- Securities (Chứng khoán): Benefiting from market growth but volatile\n"
        "- Retail & Consumer: Growing middle class driving consumption\n"
        "- Manufacturing & Export: FDI-driven, sensitive to global trade\n\n"

        "**Key Ratios to Analyze (with Vietnam context):**\n"
        "- P/E Ratio: Compare to VN-Index average (~12-15x historically)\n"
        "- P/B Ratio: Important for banking stocks\n"
        "- ROE: Strong indicator for Vietnamese companies (>15% is good)\n"
        "- Debt/Equity: Monitor carefully as Vietnam companies tend to have higher leverage\n"
        "- Dividend Yield: Vietnamese investors value dividends highly\n\n"

        "Provide detailed, actionable insights that help traders make informed decisions. "
        "Do not simply state trends are mixed - provide specific analysis with numbers and context. "
        "Make sure to append a Markdown table at the end of the report to organize key points, organized and easy to read.\n\n"
        "Use the available tools: `get_fundamentals` for comprehensive company analysis, `get_balance_sheet`, `get_cashflow`, and `get_income_statement` for specific financial statements."
    )


def create_fundamentals_analyst(llm):
    """Create a fundamentals analyst node for the trading agents graph.

    The fundamentals analyst examines company financial documents and health.
    When configured for Vietnam market (market='vn'), it uses Vietnam-specific
    financial context including:
    - Vietnamese accounting standards (VAS) context
    - Vietnam-specific sectors (banking, real estate)
    - Vietnamese financial document terminology

    Args:
        llm: The language model to use for analysis

    Returns:
        A node function for the trading agents graph
    """
    def fundamentals_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_fundamentals,
            get_balance_sheet,
            get_cashflow,
            get_income_statement,
        ]

        # Check if we're in Vietnam market mode
        config = get_config()
        market = config.get("market", "us").lower()

        # Select appropriate system message based on market
        if market == "vn":
            system_message = _get_vn_fundamentals_system_message()
        else:
            system_message = _get_us_fundamentals_system_message()

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
            "fundamentals_report": report,
        }

    return fundamentals_analyst_node
