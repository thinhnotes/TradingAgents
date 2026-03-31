"""Vietnam stock data provider using vnstock library.

Provides OHLCV, fundamentals, listings, and VNIndex data for HOSE tickers.
vnstock is imported lazily — system won't break if not installed.
"""

from typing import Annotated
from datetime import datetime


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
        stock = Vnstock().stock(symbol=symbol.upper(), source='TCBS')
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
        header += f"# Source: vnstock (TCBS)\n"
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
        stock = Vnstock().stock(symbol=ticker.upper(), source='TCBS')
        overview = stock.company.overview()

        if overview is None or (hasattr(overview, 'empty') and overview.empty):
            return f"No fundamentals data found for symbol '{ticker}'"

        # Format as key-value string
        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Source: vnstock (TCBS)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if hasattr(overview, 'to_dict'):
            # DataFrame — convert first row to dict
            if hasattr(overview, 'iloc'):
                info = overview.iloc[0].to_dict() if len(overview) > 0 else {}
            else:
                info = overview.to_dict()
        elif isinstance(overview, dict):
            info = overview
        else:
            return header + str(overview)

        lines = []
        for key, value in info.items():
            if value is not None and str(value).strip():
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
        stock = Vnstock().stock(symbol=ticker.upper(), source='TCBS')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.balance_sheet(period=period)

        if data is None or data.empty:
            return f"No balance sheet data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (TCBS)\n"
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
        stock = Vnstock().stock(symbol=ticker.upper(), source='TCBS')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.cash_flow(period=period)

        if data is None or data.empty:
            return f"No cash flow data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (TCBS)\n"
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
        stock = Vnstock().stock(symbol=ticker.upper(), source='TCBS')
        period = 'quarterly' if freq.lower() == 'quarterly' else 'annual'
        data = stock.finance.income_statement(period=period)

        if data is None or data.empty:
            return f"No income statement data found for symbol '{ticker}'"

        csv_string = data.to_csv(index=False)

        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vnstock (TCBS)\n"
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
    curr_date: Annotated[str, "current date"] = None,
    look_back_days: Annotated[int, "days to look back"] = 7,
) -> str:
    """Stub: Vietnamese news integration planned for Phase 5."""
    return (
        f"# News for {ticker.upper()}\n"
        f"# Source: vnstock\n\n"
        f"Vietnamese financial news integration is planned for Phase 5. "
        f"Currently, news data is not available for HOSE tickers through this provider."
    )


def get_global_news() -> str:
    """Stub: Vietnamese global news integration planned for Phase 5."""
    return (
        "# Vietnamese Market Global News\n"
        "# Source: vnstock\n\n"
        "Vietnamese global market news integration is planned for Phase 5. "
        "Currently, global news for the Vietnamese market is not available."
    )


def get_vnindex_data(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get VNIndex composite data via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(symbol='VNINDEX', source='TCBS')
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
        header += f"# Source: vnstock (TCBS)\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving VNIndex data via vnstock: {str(e)}"


def get_available_tickers() -> list:
    """Get list of all available HOSE tickers via vnstock."""
    try:
        Vnstock = _get_vnstock()
        stock = Vnstock().stock(source='TCBS')
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
