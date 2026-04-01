"""Vietnam stock data provider using vnstock library.

Provides OHLCV, fundamentals, listings, and VNIndex data for HOSE tickers.
vnstock is imported lazily — system won't break if not installed.
"""

from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd


def _get_vnstock():
    """Lazily import and return vnstock module."""
    try:
        from vnstock import Vnstock
        return Vnstock
    except ImportError:
        raise ImportError(
            "vnstock is required for Vietnamese market data. "
            "Install it with: pip install vnstock"
        )


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company (e.g., 'FPT', 'VNM')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get OHLCV stock data for a HOSE ticker via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=symbol.upper(), source='VCI')
        data = stock.quote.history(start=start_date, end=end_date)

        if data is None or data.empty:
            return (
                f"No data found for symbol '{symbol}' between {start_date} and {end_date}"
            )

        # Standardize column names for consistency with yfinance output
        column_map = {
            'time': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        }
        data = data.rename(columns={k: v for k, v in column_map.items() if k in data.columns})

        # Round numerical values
        numeric_cols = ['Open', 'High', 'Low', 'Close']
        for col in numeric_cols:
            if col in data.columns:
                data[col] = data[col].round(2)

        csv_string = data.to_csv(index=False)

        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Currency: VND\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving stock data for {symbol} via vnstock: {str(e)}"


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used)"] = None,
) -> str:
    """Get company fundamentals overview via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        overview = stock.company.overview()

        if overview is None or (hasattr(overview, 'empty') and overview.empty):
            return f"No fundamentals data found for symbol '{ticker}'"

        # Format as key-value string
        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Standardize keys for agent compatibility (match yfinance where possible)
        key_map = {
            'market_cap': 'Market Cap',
            'pe': 'PE Ratio (TTM)',
            'pb': 'Price to Book',
            'dividend_yield': 'Dividend Yield',
            'industry': 'Industry',
            'revenue_ttm': 'Revenue (TTM)',
            'profit_ttm': 'Net Income',
            'eps_ttm': 'EPS (TTM)',
            'beta': 'Beta',
            'outstanding_shares': 'Shares Outstanding',
            'high_52w': '52 Week High',
            'low_52w': '52 Week Low',
        }

        if hasattr(overview, 'to_dict'):
            # DataFrame — convert first row to dict
            if hasattr(overview, 'iloc') and len(overview) > 0:
                info = overview.iloc[0].to_dict()
            else:
                info = overview.to_dict()
        elif isinstance(overview, dict):
            info = overview
        else:
            return header + str(overview)

        lines = []
        processed_keys = set()
        for vn_key, display_name in key_map.items():
            if vn_key in info:
                val = info[vn_key]
                if val is not None:
                    lines.append(f"{display_name}: {val}")
                processed_keys.add(vn_key)
        
        for key, value in info.items():
            if key not in processed_keys and value is not None and str(value).strip():
                lines.append(f"{key}: {value}")

        return header + "\n".join(lines)


    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving fundamentals for {ticker} via vnstock: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get balance sheet data via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.balance_sheet(period=period)

        if data is None or data.empty:
            return f"No balance sheet data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving balance sheet for {ticker} via vnstock: {str(e)}"


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get cash flow data via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.cash_flow(period=period)

        if data is None or data.empty:
            return f"No cash flow data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving cash flow for {ticker} via vnstock: {str(e)}"


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get income statement data via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.income_statement(period=period)

        if data is None or data.empty:
            return f"No income statement data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving income statement for {ticker} via vnstock: {str(e)}"


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"],
) -> str:
    """Insider transactions are not available for Vietnamese stocks."""
    return (
        f"# Insider Transactions for {ticker.upper()}\n"
        f"# Source: vnstock\n\n"
        f"Insider transaction data is not available for Vietnamese stocks (HOSE). "
        f"This data type is specific to US markets (SEC filings)."
    )


def get_news(
    ticker: Annotated[str, "ticker symbol"],
    start_date: Annotated[str, "start date in yyyy-mm-dd"],
    end_date: Annotated[str, "end date in yyyy-mm-dd"],
) -> str:
    """Retrieve news for a HOSE ticker via vnstock, filtered by date range."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol=ticker.upper(), source='VCI')
        news = stock.company.news()

        if news is None or (hasattr(news, 'empty') and news.empty):
            return f"No news found for symbol '{ticker}'"

        # Calculate date range for filtering
        # Multi-index or complex column names check
        if isinstance(news.columns, pd.MultiIndex):
            news.columns = news.columns.get_level_values(-1)

        # Parse date range for filtering
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        news_str = ""
        count = 0

        # Mapping: news_title, public_date, news_short_content
        for _, row in news.iterrows():
            pub_date_str = str(row.get('public_date', ''))
            pub_date = None
            if pub_date_str:
                try:
                    # Clean up date format if needed
                    pub_date = datetime.fromisoformat(pub_date_str.split(' ')[0])
                except Exception:
                    pass

            # Filter by date
            if pub_date and not (start_dt <= pub_date <= end_dt + relativedelta(days=1)):
                continue

            title = row.get('news_title', 'No Title')
            content = row.get('news_short_content', '')
            link = row.get('news_source_link', '')

            news_str += f"### {title}\n"
            if content:
                news_str += f"{content}\n"
            if link:
                news_str += f"Link: {link}\n"
            news_str += "\n"
            count += 1
            if count >= 10:  # Limit to 10 articles
                break

        if count == 0:
            return f"No news found for {ticker.upper()} between {start_date} and {end_date}."

        header = f"## {ticker.upper()} News, from {start_date} to {end_date}:\n"
        header += f"# Source: vnstock (VCI)\n\n"

        return header + news_str

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving news for {ticker} via vnstock: {str(e)}"


def get_global_news() -> str:
    """Retrieve global/macro news for VN market (Placeholder for VNIndex context)."""
    return (
        "# Vietnamese Market Global News\n"
        "# Source: vnstock\n\n"
        "Global market news for Vietnam is currently summarized through VNIndex analysis. "
        "Specific macro news headlines are scheduled for full integration in Phase 5."
    )


def get_vnindex_data(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get VNIndex composite data via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol='VNINDEX', source='VCI')
        data = stock.quote.history(start=start_date, end=end_date)

        if data is None or data.empty:
            return (
                f"No VNIndex data found between {start_date} and {end_date}"
            )

        # Standardize column names
        column_map = {
            'time': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
        }
        data = data.rename(columns={k: v for k, v in column_map.items() if k in data.columns})

        csv_string = data.to_csv(index=False)

        header = f"# VNIndex Composite Data from {start_date} to {end_date}\n"
        header += f"# Source: vnstock (VCI)\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving VNIndex data via vnstock: {str(e)}"


def get_global_news(
    curr_date: Annotated[str, "current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "number of days to look back"] = 7,
    limit: Annotated[int, "maximum number of articles to return"] = 5,
) -> str:
    """Stub: Global news not directly available via vnstock."""
    start_dt = datetime.strptime(curr_date, "%Y-%m-%d") - relativedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")
    return (
        f"## Global Market News, from {start_date} to {curr_date}:\n\n"
        f"Global macro news is not available via vnstock provider. "
        f"Falling back to US market data tools for global sentiment."
    )


def get_available_tickers() -> list:
    """Get list of all available HOSE tickers via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(source='VCI')
        listing = stock.listing.all_symbols()

        if listing is None or (hasattr(listing, 'empty') and listing.empty):
            return []

        # Extract ticker symbols from listing DataFrame
        if hasattr(listing, 'to_list'):
            return listing.to_list()
        elif hasattr(listing, 'values'):
            # DataFrame — try to get the symbol/ticker column
            for col in ['ticker', 'symbol', 'code']:
                if col in listing.columns:
                    return listing[col].tolist()
            # Fallback: return first column
            return listing.iloc[:, 0].tolist()
        else:
            return list(listing)

    except ImportError:
        raise
    except Exception as e:
        print(f"Error retrieving available tickers via vnstock: {str(e)}")
        return []
