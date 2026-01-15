"""
vnstock.py - Data fetching module for Vietnamese stock market data.

This module provides functions to fetch stock data from the Vietnamese stock market
using the vnstock3 library. It mirrors the interface of the yfinance module to enable
seamless vendor routing.

Supported exchanges: HOSE, HNX, UPCOM

Caching:
- Stock OHLCV data: 1 hour TTL
- Financial statements: 24 hours TTL (quarterly data)
- Company overview: 1 week TTL (rarely changes)
- Technical indicators: 24 hours TTL
"""

from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

# Import caching utilities
from .cache import (
    get_cache,
    generate_cache_key,
    get_ttl_for_category,
    DEFAULT_STOCK_TTL_SECONDS,
    DEFAULT_INDICATORS_TTL_SECONDS,
)

# Try to import vnstock3, with graceful fallback for environments without it installed
try:
    from vnstock3 import Vnstock
    VNSTOCK_AVAILABLE = True
except ImportError:
    VNSTOCK_AVAILABLE = False


# TTL constants for VN stock data (in seconds)
VN_STOCK_DATA_TTL = DEFAULT_STOCK_TTL_SECONDS  # 1 hour
VN_FUNDAMENTALS_TTL = 86400  # 24 hours for financial statements
VN_COMPANY_OVERVIEW_TTL = 604800  # 1 week for company info
VN_INDICATORS_TTL = DEFAULT_INDICATORS_TTL_SECONDS  # 24 hours


def _check_vnstock_available():
    """Check if vnstock3 library is available."""
    if not VNSTOCK_AVAILABLE:
        raise ImportError(
            "vnstock3 library is not installed. "
            "Install it with: pip install vnstock3"
        )


def _get_stock_instance(symbol: str, source: str = "VCI"):
    """
    Create a vnstock stock instance for the given symbol.

    Args:
        symbol: Vietnamese stock ticker symbol (e.g., 'VNM', 'FPT', 'TCB')
        source: Data source to use ('VCI', 'TCBS', 'MSN'). Default is 'VCI'.

    Returns:
        Stock instance from vnstock3
    """
    _check_vnstock_available()
    stock = Vnstock().stock(symbol=symbol.upper(), source=source)
    return stock


def get_vnstock_data(
    symbol: Annotated[str, "ticker symbol of the company (e.g., VNM, FPT, TCB)"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Fetch historical OHLCV stock data for Vietnamese stocks.

    This function mirrors get_YFin_data_online for Vietnamese market stocks.
    Results are cached for 1 hour to reduce API calls.

    Args:
        symbol: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        CSV string with header information and OHLCV data
    """
    _check_vnstock_available()

    # Validate date format
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_stock_data",
        ticker=symbol.upper(),
        start_date=start_date,
        end_date=end_date
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(symbol)

        # Fetch historical data
        data = stock.quote.history(start=start_date, end=end_date)

        if data is None or data.empty:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

        # Standardize column names to match yfinance output format
        # vnstock returns: time, open, high, low, close, volume
        column_mapping = {
            'time': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }

        # Rename columns if they exist (vnstock may use different casing)
        data.columns = data.columns.str.lower()
        data = data.rename(columns=column_mapping)

        # Round numerical values to 2 decimal places for cleaner display
        numeric_columns = ["Open", "High", "Low", "Close"]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = data[col].round(2)

        # Convert DataFrame to CSV string
        csv_string = data.to_csv(index=False)

        # Add header information
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Total records: {len(data)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_STOCK_DATA_TTL)

        return result

    except Exception as e:
        return f"Error retrieving data for {symbol}: {str(e)}"


def get_vnstock_balance_sheet(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """
    Get balance sheet data from vnstock for Vietnamese stocks.

    This function mirrors get_balance_sheet from yfinance for Vietnamese market stocks.
    Results are cached for 24 hours to reduce API calls.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        freq: Reporting frequency - 'annual' or 'quarterly'
        curr_date: Current date (not used, included for interface compatibility)

    Returns:
        CSV string with balance sheet data
    """
    _check_vnstock_available()

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_balance_sheet",
        ticker=ticker.upper(),
        freq=freq.lower()
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(ticker)

        # Get balance sheet - vnstock uses 'year' or 'quarter' for period
        period = "quarter" if freq.lower() == "quarterly" else "year"
        data = stock.finance.balance_sheet(period=period)

        if data is None or data.empty:
            return f"No balance sheet data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv(index=False)

        # Add header information
        header = f"# Balance Sheet data for {ticker.upper()} ({freq})\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_FUNDAMENTALS_TTL)

        return result

    except Exception as e:
        return f"Error retrieving balance sheet for {ticker}: {str(e)}"


def get_vnstock_cashflow(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """
    Get cash flow statement data from vnstock for Vietnamese stocks.

    This function mirrors get_cashflow from yfinance for Vietnamese market stocks.
    Results are cached for 24 hours to reduce API calls.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        freq: Reporting frequency - 'annual' or 'quarterly'
        curr_date: Current date (not used, included for interface compatibility)

    Returns:
        CSV string with cash flow data
    """
    _check_vnstock_available()

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_cashflow",
        ticker=ticker.upper(),
        freq=freq.lower()
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(ticker)

        # Get cash flow - vnstock uses 'year' or 'quarter' for period
        period = "quarter" if freq.lower() == "quarterly" else "year"
        data = stock.finance.cash_flow(period=period)

        if data is None or data.empty:
            return f"No cash flow data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv(index=False)

        # Add header information
        header = f"# Cash Flow data for {ticker.upper()} ({freq})\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_FUNDAMENTALS_TTL)

        return result

    except Exception as e:
        return f"Error retrieving cash flow for {ticker}: {str(e)}"


def get_vnstock_income_statement(
    ticker: Annotated[str, "ticker symbol of the company"],
    freq: Annotated[str, "frequency of data: 'annual' or 'quarterly'"] = "quarterly",
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """
    Get income statement data from vnstock for Vietnamese stocks.

    This function mirrors get_income_statement from yfinance for Vietnamese market stocks.
    Results are cached for 24 hours to reduce API calls.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        freq: Reporting frequency - 'annual' or 'quarterly'
        curr_date: Current date (not used, included for interface compatibility)

    Returns:
        CSV string with income statement data
    """
    _check_vnstock_available()

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_income_statement",
        ticker=ticker.upper(),
        freq=freq.lower()
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(ticker)

        # Get income statement - vnstock uses 'year' or 'quarter' for period
        period = "quarter" if freq.lower() == "quarterly" else "year"
        data = stock.finance.income_statement(period=period)

        if data is None or data.empty:
            return f"No income statement data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv(index=False)

        # Add header information
        header = f"# Income Statement data for {ticker.upper()} ({freq})\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_FUNDAMENTALS_TTL)

        return result

    except Exception as e:
        return f"Error retrieving income statement for {ticker}: {str(e)}"


def get_vnstock_financial_ratios(
    ticker: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "current date (not used for vnstock)"] = None
) -> str:
    """
    Get financial ratios (P/E, P/B, ROE, etc.) for Vietnamese stocks.

    This provides additional fundamental data specific to Vietnamese market.
    Results are cached for 24 hours to reduce API calls.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        curr_date: Current date (not used, included for interface compatibility)

    Returns:
        CSV string with financial ratio data
    """
    _check_vnstock_available()

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_financial_ratios",
        ticker=ticker.upper()
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(ticker)

        # Get financial ratios
        data = stock.finance.ratio()

        if data is None or data.empty:
            return f"No financial ratio data found for symbol '{ticker}'"

        # Convert to CSV string for consistency with other functions
        csv_string = data.to_csv(index=False)

        # Add header information
        header = f"# Financial Ratios for {ticker.upper()}\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Includes: P/E, P/B, ROE, ROA, EPS, etc.\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_FUNDAMENTALS_TTL)

        return result

    except Exception as e:
        return f"Error retrieving financial ratios for {ticker}: {str(e)}"


def get_vnstock_company_overview(
    ticker: Annotated[str, "ticker symbol of the company"]
) -> str:
    """
    Get company overview/profile for Vietnamese stocks.

    This provides company information similar to yfinance's ticker.info.
    Results are cached for 1 week since company info rarely changes.

    Args:
        ticker: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')

    Returns:
        Formatted string with company overview data
    """
    _check_vnstock_available()

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_company_overview",
        ticker=ticker.upper()
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        stock = _get_stock_instance(ticker)

        # Get company overview
        data = stock.company.overview()

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            return f"No company overview data found for symbol '{ticker}'"

        # Convert to CSV if DataFrame, otherwise format as string
        if isinstance(data, pd.DataFrame):
            csv_string = data.to_csv(index=False)
        else:
            # If it's a dict or other format, convert to readable format
            csv_string = str(data)

        # Add header information
        header = f"# Company Overview for {ticker.upper()}\n"
        header += f"# Market: Vietnam (HOSE/HNX/UPCOM)\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        result = header + csv_string

        # Cache the result
        cache.set(cache_key, result, ttl_seconds=VN_COMPANY_OVERVIEW_TTL)

        return result

    except Exception as e:
        return f"Error retrieving company overview for {ticker}: {str(e)}"


def get_vnstock_indicators(
    symbol: Annotated[str, "ticker symbol of the company (e.g., VNM, FPT, TCB)"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """
    Get technical indicators for Vietnamese stocks using vnstock data and stockstats.

    This function mirrors get_stock_stats_indicators_window for Vietnamese market stocks.
    It fetches OHLCV data from vnstock and uses stockstats library to calculate
    technical indicators. Results are cached for 24 hours.

    Args:
        symbol: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        indicator: Technical indicator to calculate (e.g., 'rsi', 'macd', 'close_50_sma')
        curr_date: Current trading date in YYYY-MM-DD format
        look_back_days: Number of days to look back for indicator values

    Returns:
        String containing indicator values over the time window with descriptions

    Supported indicators:
        - Moving Averages: close_50_sma, close_200_sma, close_10_ema
        - MACD: macd, macds, macdh
        - Momentum: rsi, mfi
        - Volatility: boll, boll_ub, boll_lb, atr
        - Volume: vwma
    """
    _check_vnstock_available()

    # Import stockstats for indicator calculation
    try:
        from stockstats import wrap
    except ImportError:
        raise ImportError(
            "stockstats library is not installed. "
            "Install it with: pip install stockstats"
        )

    # Indicator descriptions (same as yfinance implementation for consistency)
    best_ind_params = {
        # Moving Averages
        "close_50_sma": (
            "50 SMA: A medium-term trend indicator. "
            "Usage: Identify trend direction and serve as dynamic support/resistance. "
            "Tips: It lags price; combine with faster indicators for timely signals."
        ),
        "close_200_sma": (
            "200 SMA: A long-term trend benchmark. "
            "Usage: Confirm overall market trend and identify golden/death cross setups. "
            "Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries."
        ),
        "close_10_ema": (
            "10 EMA: A responsive short-term average. "
            "Usage: Capture quick shifts in momentum and potential entry points. "
            "Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals."
        ),
        # MACD Related
        "macd": (
            "MACD: Computes momentum via differences of EMAs. "
            "Usage: Look for crossovers and divergence as signals of trend changes. "
            "Tips: Confirm with other indicators in low-volatility or sideways markets."
        ),
        "macds": (
            "MACD Signal: An EMA smoothing of the MACD line. "
            "Usage: Use crossovers with the MACD line to trigger trades. "
            "Tips: Should be part of a broader strategy to avoid false positives."
        ),
        "macdh": (
            "MACD Histogram: Shows the gap between the MACD line and its signal. "
            "Usage: Visualize momentum strength and spot divergence early. "
            "Tips: Can be volatile; complement with additional filters in fast-moving markets."
        ),
        # Momentum Indicators
        "rsi": (
            "RSI: Measures momentum to flag overbought/oversold conditions. "
            "Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. "
            "Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis."
        ),
        # Volatility Indicators
        "boll": (
            "Bollinger Middle: A 20 SMA serving as the basis for Bollinger Bands. "
            "Usage: Acts as a dynamic benchmark for price movement. "
            "Tips: Combine with the upper and lower bands to effectively spot breakouts or reversals."
        ),
        "boll_ub": (
            "Bollinger Upper Band: Typically 2 standard deviations above the middle line. "
            "Usage: Signals potential overbought conditions and breakout zones. "
            "Tips: Confirm signals with other tools; prices may ride the band in strong trends."
        ),
        "boll_lb": (
            "Bollinger Lower Band: Typically 2 standard deviations below the middle line. "
            "Usage: Indicates potential oversold conditions. "
            "Tips: Use additional analysis to avoid false reversal signals."
        ),
        "atr": (
            "ATR: Averages true range to measure volatility. "
            "Usage: Set stop-loss levels and adjust position sizes based on current market volatility. "
            "Tips: It's a reactive measure, so use it as part of a broader risk management strategy."
        ),
        # Volume-Based Indicators
        "vwma": (
            "VWMA: A moving average weighted by volume. "
            "Usage: Confirm trends by integrating price action with volume data. "
            "Tips: Watch for skewed results from volume spikes; use in combination with other volume analyses."
        ),
        "mfi": (
            "MFI: The Money Flow Index is a momentum indicator that uses both price and volume to measure buying and selling pressure. "
            "Usage: Identify overbought (>80) or oversold (<20) conditions and confirm the strength of trends or reversals. "
            "Tips: Use alongside RSI or MACD to confirm signals; divergence between price and MFI can indicate potential reversals."
        ),
    }

    if indicator not in best_ind_params:
        raise ValueError(
            f"Indicator {indicator} is not supported. Please choose from: {list(best_ind_params.keys())}"
        )

    # Generate cache key
    cache = get_cache()
    cache_key = generate_cache_key(
        "vn_indicators",
        ticker=symbol.upper(),
        indicator=indicator,
        curr_date=curr_date,
        look_back_days=look_back_days
    )

    # Try to get from cache first
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    try:
        # Parse dates
        curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
        before = curr_date_dt - relativedelta(days=look_back_days)

        # Get indicator data using bulk calculation
        indicator_data = _get_vnstock_indicators_bulk(symbol, indicator, curr_date)

        # Generate the date range we need
        current_dt = curr_date_dt
        date_values = []

        while current_dt >= before:
            date_str = current_dt.strftime('%Y-%m-%d')

            # Look up the indicator value for this date
            if date_str in indicator_data:
                indicator_value = indicator_data[date_str]
            else:
                indicator_value = "N/A: Not a trading day (weekend or holiday)"

            date_values.append((date_str, indicator_value))
            current_dt = current_dt - relativedelta(days=1)

        # Build the result string
        ind_string = ""
        for date_str, value in date_values:
            ind_string += f"{date_str}: {value}\n"

        result_str = (
            f"## {indicator} values from {before.strftime('%Y-%m-%d')} to {curr_date}:\n\n"
            + ind_string
            + "\n\n"
            + best_ind_params.get(indicator, "No description available.")
        )

        # Cache the result
        cache.set(cache_key, result_str, ttl_seconds=VN_INDICATORS_TTL)

        return result_str

    except Exception as e:
        return f"Error calculating {indicator} for {symbol}: {str(e)}"


def _get_vnstock_indicators_bulk(
    symbol: str,
    indicator: str,
    curr_date: str
) -> dict:
    """
    Optimized bulk calculation of technical indicators for vnstock data.

    Fetches OHLCV data from vnstock once and calculates indicator for all
    available dates using stockstats library.

    Args:
        symbol: Vietnamese stock ticker (e.g., 'VNM', 'FPT', 'TCB')
        indicator: Technical indicator to calculate
        curr_date: Current date for reference

    Returns:
        dict mapping date strings to indicator values
    """
    from stockstats import wrap
    import os
    from .config import get_config, DATA_DIR

    _check_vnstock_available()

    config = get_config()

    # Calculate date range - get enough historical data for indicator calculation
    # Most indicators need at least 200 days of historical data (for 200 SMA)
    curr_date_dt = pd.to_datetime(curr_date)
    today_date = pd.Timestamp.today()

    # Use 2 years of data to ensure enough history for all indicators
    end_date = min(curr_date_dt, today_date)
    start_date = end_date - pd.DateOffset(years=2)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Check cache directory for cached data
    cache_dir = config.get("data_cache_dir", DATA_DIR)
    os.makedirs(cache_dir, exist_ok=True)

    data_file = os.path.join(
        cache_dir,
        f"{symbol.upper()}-vnstock-data-{start_date_str}-{end_date_str}.csv",
    )

    data = None

    # Try to load from cache first
    if os.path.exists(data_file):
        try:
            data = pd.read_csv(data_file)
            data["Date"] = pd.to_datetime(data["Date"])
        except Exception:
            data = None

    # If no cache, fetch from vnstock
    if data is None:
        stock = _get_stock_instance(symbol)

        # Fetch historical data
        raw_data = stock.quote.history(start=start_date_str, end=end_date_str)

        if raw_data is None or raw_data.empty:
            raise ValueError(f"No data found for symbol '{symbol}' between {start_date_str} and {end_date_str}")

        # Standardize column names to match stockstats expectations
        # vnstock returns: time, open, high, low, close, volume
        # stockstats expects: Date, Open, High, Low, Close, Volume (or lowercase equivalents)
        raw_data.columns = raw_data.columns.str.lower()

        column_mapping = {
            'time': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }

        data = raw_data.rename(columns=column_mapping)

        # Ensure Date is proper datetime
        data["Date"] = pd.to_datetime(data["Date"])

        # Save to cache
        try:
            data.to_csv(data_file, index=False)
        except Exception:
            pass  # Cache write failure is non-critical

    # Wrap DataFrame with stockstats for indicator calculation
    df = wrap(data)

    # Format Date as string for lookup
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Calculate the indicator (triggers stockstats calculation)
    try:
        df[indicator]
    except Exception as e:
        raise ValueError(f"Failed to calculate indicator '{indicator}': {str(e)}")

    # Create a dictionary mapping date strings to indicator values
    result_dict = {}
    for _, row in df.iterrows():
        date_str = row["Date"]
        indicator_value = row[indicator]

        # Handle NaN/None values
        if pd.isna(indicator_value):
            result_dict[date_str] = "N/A"
        else:
            result_dict[date_str] = str(round(indicator_value, 4))

    return result_dict
