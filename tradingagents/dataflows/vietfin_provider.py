"""Vietnam stock data provider using vietfin library.

Secondary data source for cross-validation of Vietnamese stock data.
vietfin is imported lazily — system won't break if not installed.
"""

from typing import Annotated
from datetime import datetime


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


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company (e.g., 'FPT', 'VNM')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get historical stock data for a HOSE ticker via vietfin."""
    try:
        vf = _get_vietfin()
        result = vf.equity.historical(symbol=symbol.lower(), start=start_date, end=end_date)

        if result is None:
            return (
                f"No data found for symbol '{symbol}' via vietfin "
                f"between {start_date} and {end_date}"
            )

        # vietfin returns OBBject with .to_df() or similar
        if hasattr(result, 'to_df'):
            data = result.to_df()
        elif hasattr(result, 'results') and result.results:
            import pandas as pd
            data = pd.DataFrame([vars(r) if hasattr(r, '__dict__') else r for r in result.results])
        else:
            return f"No data found for symbol '{symbol}' via vietfin"

        if data.empty:
            return f"No data found for symbol '{symbol}' via vietfin"

        csv_string = data.to_csv(index=False)

        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Source: vietfin\n"
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

        # Fetch profile and ratios
        profile = vf.equity.profile(symbol=ticker.lower())
        ratios = None
        try:
            ratios = vf.equity.fundamental.ratios(symbol=ticker.lower())
        except Exception:
            pass  # Ratios may not be available

        header = f"# Company Fundamentals for {ticker.upper()}\n"
        header += f"# Source: vietfin\n"
        header += f"# Currency: VND\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        lines = []

        # Extract profile data
        if profile is not None:
            if hasattr(profile, 'to_df'):
                df = profile.to_df()
                if not df.empty:
                    for col in df.columns:
                        val = df[col].iloc[0] if len(df) > 0 else None
                        if val is not None and str(val).strip():
                            lines.append(f"{col}: {val}")
            elif hasattr(profile, 'results') and profile.results:
                for item in profile.results:
                    if hasattr(item, '__dict__'):
                        for key, val in vars(item).items():
                            if val is not None and str(val).strip():
                                lines.append(f"{key}: {val}")

        # Extract ratios data
        if ratios is not None:
            lines.append("\n--- Financial Ratios ---")
            if hasattr(ratios, 'to_df'):
                df = ratios.to_df()
                if not df.empty:
                    for col in df.columns:
                        val = df[col].iloc[0] if len(df) > 0 else None
                        if val is not None and str(val).strip():
                            lines.append(f"{col}: {val}")

        if not lines:
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
        result = vf.equity.fundamental.income(symbol=ticker.lower())

        if result is None:
            return f"No income statement data found for symbol '{ticker}' via vietfin"

        if hasattr(result, 'to_df'):
            data = result.to_df()
        elif hasattr(result, 'results') and result.results:
            import pandas as pd
            data = pd.DataFrame([vars(r) if hasattr(r, '__dict__') else r for r in result.results])
        else:
            return f"No income statement data found for symbol '{ticker}' via vietfin"

        if data.empty:
            return f"No income statement data found for symbol '{ticker}' via vietfin"

        csv_string = data.to_csv(index=False)

        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Source: vietfin\n"
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
    """Balance sheet not available via vietfin."""
    return (
        f"# Balance Sheet data for {ticker.upper()}\n"
        f"# Source: vietfin\n\n"
        f"Balance sheet data is not available via vietfin. "
        f"Use vnstock as the primary data source for balance sheet data."
    )


def get_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date in YYYY-MM-DD format"] = None,
) -> str:
    """Cash flow data not available via vietfin."""
    return (
        f"# Cash Flow data for {ticker.upper()}\n"
        f"# Source: vietfin\n\n"
        f"Cash flow data is not available via vietfin. "
        f"Use vnstock as the primary data source for cash flow data."
    )


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
    curr_date: Annotated[str, "current date"] = None,
    look_back_days: Annotated[int, "days to look back"] = 7,
) -> str:
    """Stub: Vietnamese news not available via vietfin."""
    return (
        f"# News for {ticker.upper()}\n"
        f"# Source: vietfin\n\n"
        f"Vietnamese financial news is not available via vietfin. "
        f"News integration planned for Phase 5."
    )


def get_global_news() -> str:
    """Stub: Global news not available via vietfin."""
    return (
        "# Vietnamese Market Global News\n"
        "# Source: vietfin\n\n"
        "Global market news is not available via vietfin."
    )
