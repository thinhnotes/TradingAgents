"""Vietnam stock data provider using vietfin library.

Secondary data source for cross-validation of Vietnamese stock data.
vietfin is imported lazily — system won't break if not installed.

API reference (vietfin v0.2.x):
  vf.equity.price.historical(symbol, start_date, end_date, interval, provider)
  vf.equity.profile(symbol, provider)
  vf.equity.fundamental.ratios(symbol, period, provider)
  vf.equity.fundamental.income(symbol, period, provider)
  vf.equity.fundamental.balance(symbol, period, provider)
  vf.equity.fundamental.cash(symbol, period, provider)
"""

from typing import Annotated
from datetime import datetime

# Provider priority: dnse works best for price data, tcbs for fundamentals
_PRICE_PROVIDERS = ['dnse', 'tcbs', 'ssi']
_FUNDAMENTAL_PROVIDERS = ['tcbs', 'ssi']


def _get_vietfin():
    """Lazily import and return vietfin module."""
    try:
        from vietfin import vf
        return vf
    except ImportError:
        raise ImportError(
            "vietfin is required for Vietnamese market cross-validation. "
            "Install it with: pip install vietfin"
        )


def _vfobject_to_df(result):
    """Convert a VfObject result to a pandas DataFrame."""
    if result is None:
        return None

    import pandas as pd

    if hasattr(result, 'to_df'):
        return result.to_df()
    elif hasattr(result, 'results') and result.results:
        return pd.DataFrame([
            vars(r) if hasattr(r, '__dict__') else r
            for r in result.results
        ])
    return None


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company (e.g., 'FPT', 'VNM')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get historical stock data for a HOSE ticker via vietfin."""
    try:
        vf = _get_vietfin()

        # Try each price provider until one works
        last_error = None
        used_provider = None
        for provider in _PRICE_PROVIDERS:
            try:
                result = vf.equity.price.historical(
                    symbol=symbol.lower(),
                    start_date=start_date,
                    end_date=end_date,
                    interval='1d',
                    provider=provider,
                )
                data = _vfobject_to_df(result)
                if data is not None and not data.empty:
                    used_provider = provider
                    break
            except Exception as e:
                last_error = e
                continue
        else:
            if last_error:
                return f"Error retrieving stock data for {symbol} via vietfin: {str(last_error)}"
            return (
                f"No data found for symbol '{symbol}' via vietfin "
                f"between {start_date} and {end_date}"
            )

        # Normalize column names for consistency
        col_map = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}
        data = data.rename(columns={k: v for k, v in col_map.items() if k in data.columns})

        # dnse returns prices in VND (e.g., 119890), normalize to thousands if >1000
        # to align with vnstock which returns prices like 119.89
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            if col in data.columns and data[col].mean() > 1000:
                data[col] = (data[col] / 1000).round(2)

        csv_string = data.to_csv(index=True if data.index.name else False)

        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Source: vietfin ({used_provider})\n"
        header += f"# Currency: VND\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving stock data for {symbol} via vietfin: {str(e)}"


def get_fundamentals(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used)"] = None,
) -> str:
    """Get company fundamentals via vietfin."""
    try:
        vf = _get_vietfin()

        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Source: vietfin\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        lines = []

        # Fetch profile (try each provider)
        for provider in _FUNDAMENTAL_PROVIDERS:
            try:
                profile = vf.equity.profile(symbol=ticker.lower(), provider=provider)
                df = _vfobject_to_df(profile)
                if df is not None and not df.empty:
                    lines.append(f"--- Company Profile (via {provider}) ---")
                    for col in df.columns:
                        val = df[col].iloc[0] if len(df) > 0 else None
                        if val is not None and str(val).strip():
                            lines.append(f"{col}: {val}")
                    break
            except Exception:
                continue
        if not lines:
            lines.append("Profile: unavailable (all providers failed)")

        # Fetch ratios (try each provider)
        for provider in _FUNDAMENTAL_PROVIDERS:
            try:
                ratios = vf.equity.fundamental.ratios(
                    symbol=ticker.lower(), period='annual', provider=provider
                )
                df = _vfobject_to_df(ratios)
                if df is not None and not df.empty:
                    lines.append(f"\n--- Financial Ratios (via {provider}) ---")
                    for col in df.columns:
                        val = df[col].iloc[0] if len(df) > 0 else None
                        if val is not None and str(val).strip():
                            lines.append(f"{col}: {val}")
                    break
            except Exception:
                continue

        if not lines or all('unavailable' in l for l in lines):
            return f"No fundamentals data found for symbol '{ticker}' via vietfin"

        return header + "\n".join(lines)

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving fundamentals for {ticker} via vietfin: {str(e)}"


def get_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get income statement data via vietfin."""
    try:
        vf = _get_vietfin()
        period = 'quarter' if freq.lower() == 'quarterly' else 'annual'
        result = vf.equity.fundamental.income(
            symbol=ticker.lower(), period=period, provider='tcbs'
        )

        data = _vfobject_to_df(result)
        if data is None or data.empty:
            return f"No income statement data found for symbol '{ticker}' via vietfin"

        csv_string = data.to_csv(index=False)

        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vietfin (tcbs)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving income statement for {ticker} via vietfin: {str(e)}"


def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get balance sheet data via vietfin."""
    try:
        vf = _get_vietfin()
        period = 'quarter' if freq.lower() == 'quarterly' else 'annual'
        result = vf.equity.fundamental.balance(
            symbol=ticker.lower(), period=period, provider='tcbs'
        )

        data = _vfobject_to_df(result)
        if data is None or data.empty:
            return f"No balance sheet data found for symbol '{ticker}' via vietfin"

        csv_string = data.to_csv(index=False)

        header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vietfin (tcbs)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving balance sheet for {ticker} via vietfin: {str(e)}"


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Get cash flow data via vietfin."""
    try:
        vf = _get_vietfin()
        period = 'quarter' if freq.lower() == 'quarterly' else 'annual'
        result = vf.equity.fundamental.cash(
            symbol=ticker.lower(), period=period, provider='tcbs'
        )

        data = _vfobject_to_df(result)
        if data is None or data.empty:
            return f"No cash flow data found for symbol '{ticker}' via vietfin"

        csv_string = data.to_csv(index=False)

        header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vietfin (tcbs)\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        return header + csv_string

    except ImportError:
        raise
    except Exception as e:
        return f"Error retrieving cash flow for {ticker} via vietfin: {str(e)}"


def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol of the company"],
) -> str:
    """Insider transactions not available for Vietnamese stocks."""
    return (
        f"# Insider Transactions for {ticker.upper()}\n"
        f"# Source: vietfin\n\n"
        f"Insider transaction data is not available for Vietnamese stocks via vietfin."
    )


def get_news(
    ticker: Annotated[str, "ticker symbol"],
    start_date: Annotated[str, "start date in yyyy-mm-dd"],
    end_date: Annotated[str, "end date in yyyy-mm-dd"],
) -> str:
    """Stub: Vietnamese news not available via vietfin."""
    return (
        f"# News for {ticker.upper()}\n"
        f"# Source: vietfin\n\n"
        f"Vietnamese financial news is not available via vietfin. "
        f"News integration planned for Phase 5."
    )


def get_global_news(
    curr_date: Annotated[str, "current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "number of days to look back"] = 7,
    limit: Annotated[int, "maximum number of articles to return"] = 5,
) -> str:
    """Stub: Global news not available via vietfin."""
    return (
        "# Vietnamese Market Global News\n"
        "# Source: vietfin\n\n"
        "Global market news is not available via vietfin."
    )
