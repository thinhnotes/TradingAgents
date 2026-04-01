from langchain_core.messages import HumanMessage, RemoveMessage

# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_transactions,
    get_global_news
)


def get_language_instruction() -> str:
    """Return a prompt instruction for the configured output language.

    Returns empty string when English (default), so no extra tokens are used.
    Only applied to user-facing agents (analysts, portfolio manager).
    Internal debate agents stay in English for reasoning quality.
    """
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English")
    if lang.strip().lower() == "english":
        return ""
    return (
        f" MANDATORY: You MUST write your entire response in {lang}. DO NOT use English or any other language for your analysis and report. "
        f"Internal debate history provided to you is in English. You MUST translate and synthesize this information into {lang} for your final report."
    )


def get_localized_headers() -> dict:
    """Return a dictionary of localized headers for the configured output language."""
    from tradingagents.dataflows.config import get_config
    lang = get_config().get("output_language", "English").strip().lower()
    
    # Default English headers
    headers = {
        "rating": "Rating",
        "exec_summary": "Executive Summary",
        "buy_range": "Specific Buy Price Range",
        "tp": "Take Profit (Target Price)",
        "sl": "Stop Loss",
        "time_horizon": "Expected Time Horizon",
        "sizing": "Position Sizing",
        "market_outlook": "Market Outlook & Time Horizons",
        "st": "Short-term Analysis (1-4 weeks)",
        "mt": "Medium-term Analysis (1-6 months)",
        "lt": "Long-term Analysis (> 6 months)",
        "thesis": "Investment Thesis",
        "rec": "Your Recommendation",
        "rationale": "Rationale",
        "strategic_actions": "Strategic Actions",
    }
    
    if lang == "vietnamese":
        headers.update({
            "rating": "Đánh giá",
            "exec_summary": "Tóm tắt điều hành",
            "buy_range": "Khoảng giá mua cụ thể",
            "tp": "Chốt lời (Giá mục tiêu)",
            "sl": "Dừng lỗ",
            "time_horizon": "Thời hạn dự kiến",
            "sizing": "Khuyến nghị quy mô vị thế",
            "market_outlook": "Triển vọng thị trường & Thời hạn",
            "st": "Phân tích ngắn hạn (1-4 tuần)",
            "mt": "Phân tích trung hạn (1-6 tháng)",
            "lt": "Phân tích dài hạn (> 6 tháng)",
            "thesis": "Luận điểm đầu tư",
            "rec": "Khuyến nghị của bạn",
            "rationale": "CƠ SỞ LẬP LUẬN",
            "strategic_actions": "HÀNH ĐỘNG CHIẾN LƯỢC",
        })
        
    return headers


def build_instrument_context(ticker: str) -> str:
    """Describe the exact instrument so agents preserve exchange-qualified tickers."""
    return (
        f"The instrument to analyze is `{ticker}`. "
        "Use this exact ticker in every tool call, report, and recommendation, "
        "preserving any exchange suffix (e.g. `.TO`, `.L`, `.HK`, `.T`)."
    )

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]

        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]

        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")

        return {"messages": removal_operations + [placeholder]}

    return delete_messages


        
