import sys
import os
import io
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        # Reconfigure stdout to use utf-8
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

# Load environment variables from .env file
load_dotenv()

# Create a custom config
config = DEFAULT_CONFIG.copy()
# Auto-detect LLM provider from environment
custom_url = os.getenv("CUSTOM_LLM_BASE_URL")
if custom_url:
    config["llm_provider"] = "custom"
    config["backend_url"] = custom_url

config["deep_think_llm"] = "gpt-5-mini"
config["quick_think_llm"] = "gpt-5-mini"
config["max_debate_rounds"] = 1

# Configure for Vietnamese market
config["market"] = "VN"
config["output_language"] = "Vietnamese"

# Configure data vendors (optimized for VN stocks)
config["data_vendors"] = {
    "core_stock_apis": "vnstock",
    "technical_indicators": "vnstock",
    "fundamental_data": "vnstock",
    "news_data": "vnstock",
}

import argparse
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description="TradingAgents - AI-powered stock analysis")
parser.add_argument("--ticker", type=str, default="FPT", help="Stock ticker symbol (e.g. FPT, VGI, AAPL)")
parser.add_argument("--date", type=str, default="2026-03-31", help="Analysis date in YYYY-MM-DD format")
args = parser.parse_args()

ticker = args.ticker.upper()
trade_date = args.date

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)
console = Console()

# Run the graph
console.print(Panel(f"[bold cyan]TradingAgents — VN Market Analysis[/bold cyan] for [bold yellow]{ticker}[/bold yellow]"))
try:
    final_state, decision = ta.propagate(ticker, trade_date)
    console.print(Panel(decision, title=f"Final Investment Recommendation for {ticker}", border_style="green"))
except Exception as e:
    console.print(f"[bold red]TradingAgents execution failed for {ticker}:[/bold red] {e}")
    import traceback
    traceback.print_exc()
