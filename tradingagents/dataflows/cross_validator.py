"""Cross-validation module for Vietnamese stock data sources.

Compares data from vnstock vs vietfin to detect discrepancies
and ensure data integrity. Configurable tolerance thresholds.
"""

from typing import Annotated
from datetime import datetime


def _parse_csv_to_dict(csv_string: str) -> dict:
    """Parse a CSV string (from provider output) into a dict of date -> close price.

    Expects CSV with Date and Close columns (after header comments).
    Returns dict mapping date strings to float close prices.
    """
    import pandas as pd
    from io import StringIO

    # Strip header comments (lines starting with #)
    lines = csv_string.strip().split('\n')
    data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

    if not data_lines:
        return {}

    csv_content = '\n'.join(data_lines)
    try:
        df = pd.read_csv(StringIO(csv_content))
    except Exception:
        return {}

    # Find date and close columns (case-insensitive)
    date_col = None
    close_col = None
    for col in df.columns:
        if col.lower() in ('date', 'time'):
            date_col = col
        if col.lower() == 'close':
            close_col = col

    if date_col is None or close_col is None:
        return {}

    result = {}
    for _, row in df.iterrows():
        try:
            date_str = str(row[date_col]).split(' ')[0].split('T')[0]  # Normalize date format
            close_val = float(row[close_col])
            result[date_str] = close_val
        except (ValueError, TypeError):
            continue

    return result


def validate_ohlcv(
    symbol: Annotated[str, "ticker symbol to validate"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    tolerance: Annotated[float, "tolerance as decimal (e.g., 0.01 = 1%)"] = 0.01,
) -> str:
    """Compare OHLCV data from vnstock vs vietfin for the same ticker.

    Fetches Close prices from both sources and flags dates where
    the price difference exceeds the specified tolerance.

    Args:
        symbol: HOSE ticker symbol (e.g., 'FPT')
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
        tolerance: Maximum acceptable relative difference (default 1%)

    Returns:
        Validation report as formatted string.
    """
    report_lines = [
        f"# Cross-Validation Report: {symbol.upper()}",
        f"# Date range: {start_date} to {end_date}",
        f"# Tolerance: {tolerance * 100:.1f}%",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Fetch from vnstock
    vnstock_data = {}
    vnstock_error = None
    try:
        from .vnstock_provider import get_stock_data as vnstock_get
        vnstock_csv = vnstock_get(symbol, start_date, end_date)
        vnstock_data = _parse_csv_to_dict(vnstock_csv)
    except ImportError:
        vnstock_error = "vnstock not installed"
    except Exception as e:
        vnstock_error = str(e)

    # Fetch from vietfin
    vietfin_data = {}
    vietfin_error = None
    try:
        from .vietfin_provider import get_stock_data as vietfin_get
        vietfin_csv = vietfin_get(symbol, start_date, end_date)
        vietfin_data = _parse_csv_to_dict(vietfin_csv)
    except ImportError:
        vietfin_error = "vietfin not installed"
    except Exception as e:
        vietfin_error = str(e)

    # Report source status
    report_lines.append("## Source Status")
    report_lines.append(f"- vnstock: {'OK' if vnstock_data else 'FAILED'}"
                       f"{f' ({vnstock_error})' if vnstock_error else ''}"
                       f" [{len(vnstock_data)} records]")
    report_lines.append(f"- vietfin: {'OK' if vietfin_data else 'FAILED'}"
                       f"{f' ({vietfin_error})' if vietfin_error else ''}"
                       f" [{len(vietfin_data)} records]")
    report_lines.append("")

    # Cannot validate if either source failed
    if not vnstock_data or not vietfin_data:
        report_lines.append("## Result: INCOMPLETE")
        report_lines.append("Cannot perform cross-validation — one or both sources unavailable.")
        if vnstock_data:
            report_lines.append("Using vnstock as single source (no validation possible).")
        elif vietfin_data:
            report_lines.append("Using vietfin as single source (no validation possible).")
        return "\n".join(report_lines)

    # Compare close prices for matching dates
    common_dates = sorted(set(vnstock_data.keys()) & set(vietfin_data.keys()))
    vnstock_only = sorted(set(vnstock_data.keys()) - set(vietfin_data.keys()))
    vietfin_only = sorted(set(vietfin_data.keys()) - set(vnstock_data.keys()))

    report_lines.append("## Date Coverage")
    report_lines.append(f"- Common dates: {len(common_dates)}")
    report_lines.append(f"- vnstock only: {len(vnstock_only)}")
    report_lines.append(f"- vietfin only: {len(vietfin_only)}")
    report_lines.append("")

    # Check for discrepancies
    discrepancies = []
    matches = 0
    for date in common_dates:
        vnstock_price = vnstock_data[date]
        vietfin_price = vietfin_data[date]

        if vnstock_price == 0 and vietfin_price == 0:
            matches += 1
            continue

        # Calculate relative difference
        avg_price = (vnstock_price + vietfin_price) / 2
        if avg_price == 0:
            continue

        rel_diff = abs(vnstock_price - vietfin_price) / avg_price

        if rel_diff > tolerance:
            discrepancies.append({
                'date': date,
                'vnstock': vnstock_price,
                'vietfin': vietfin_price,
                'diff_pct': rel_diff * 100,
            })
        else:
            matches += 1

    # Report discrepancies
    report_lines.append("## Validation Results")
    report_lines.append(f"- Matching prices: {matches}/{len(common_dates)}")
    report_lines.append(f"- Discrepancies: {len(discrepancies)}/{len(common_dates)}")
    report_lines.append("")

    if discrepancies:
        report_lines.append("## Discrepancies (Close Price)")
        report_lines.append("| Date | vnstock | vietfin | Diff % |")
        report_lines.append("|------|---------|---------|--------|")
        for d in discrepancies[:20]:  # Limit to 20 rows
            report_lines.append(
                f"| {d['date']} | {d['vnstock']:,.2f} | {d['vietfin']:,.2f} | {d['diff_pct']:.2f}% |"
            )
        if len(discrepancies) > 20:
            report_lines.append(f"... and {len(discrepancies) - 20} more discrepancies")
        report_lines.append("")

    # Verdict
    if not discrepancies:
        report_lines.append("## Verdict: ✅ PASS — All prices match within tolerance")
    elif len(discrepancies) / max(len(common_dates), 1) < 0.1:
        report_lines.append("## Verdict: ⚠️ MOSTLY OK — Minor discrepancies detected")
    else:
        report_lines.append("## Verdict: ❌ SIGNIFICANT DISCREPANCIES — Review data sources")

    return "\n".join(report_lines)


def validate_fundamentals(
    symbol: Annotated[str, "ticker symbol to validate"],
    tolerance: Annotated[float, "tolerance as decimal (e.g., 0.05 = 5%)"] = 0.05,
) -> str:
    """Compare fundamental data from vnstock vs vietfin.

    Args:
        symbol: HOSE ticker symbol
        tolerance: Maximum acceptable relative difference (default 5%)

    Returns:
        Validation report as formatted string.
    """
    report_lines = [
        f"# Fundamentals Cross-Validation: {symbol.upper()}",
        f"# Tolerance: {tolerance * 100:.1f}%",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Fetch from both sources
    vnstock_result = None
    vietfin_result = None

    try:
        from .vnstock_provider import get_fundamentals as vnstock_fund
        vnstock_result = vnstock_fund(symbol)
    except Exception as e:
        report_lines.append(f"vnstock fundamentals: FAILED ({e})")

    try:
        from .vietfin_provider import get_fundamentals as vietfin_fund
        vietfin_result = vietfin_fund(symbol)
    except Exception as e:
        report_lines.append(f"vietfin fundamentals: FAILED ({e})")

    if vnstock_result and vietfin_result:
        report_lines.append("## Source Status: Both available")
        report_lines.append("")
        report_lines.append("### vnstock Data")
        # Show first 500 chars of each source
        report_lines.append(vnstock_result[:500])
        report_lines.append("")
        report_lines.append("### vietfin Data")
        report_lines.append(vietfin_result[:500])
        report_lines.append("")
        report_lines.append("## Note")
        report_lines.append(
            "Fundamentals cross-validation requires manual review due to "
            "differing field names between providers. Automated numeric "
            "comparison deferred — both sources returned data successfully."
        )
    elif vnstock_result:
        report_lines.append("## Result: Partial — vnstock only")
        report_lines.append("Cannot cross-validate: vietfin data unavailable.")
    elif vietfin_result:
        report_lines.append("## Result: Partial — vietfin only")
        report_lines.append("Cannot cross-validate: vnstock data unavailable.")
    else:
        report_lines.append("## Result: FAILED — Neither source available")

    return "\n".join(report_lines)


def run_full_validation(
    symbol: Annotated[str, "ticker symbol to validate"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Run comprehensive cross-validation of OHLCV and fundamentals.

    Args:
        symbol: HOSE ticker symbol
        start_date: Start date
        end_date: End date

    Returns:
        Full validation report combining OHLCV and fundamentals checks.
    """
    from .config import get_config

    config = get_config()
    tolerance = config.get("cross_validation_tolerance", 0.01)

    report_parts = [
        "=" * 60,
        f"FULL CROSS-VALIDATION REPORT: {symbol.upper()}",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
    ]

    # OHLCV validation
    report_parts.append("SECTION 1: OHLCV DATA")
    report_parts.append("-" * 40)
    ohlcv_report = validate_ohlcv(symbol, start_date, end_date, tolerance)
    report_parts.append(ohlcv_report)
    report_parts.append("")

    # Fundamentals validation
    report_parts.append("SECTION 2: FUNDAMENTALS")
    report_parts.append("-" * 40)
    fund_report = validate_fundamentals(symbol, tolerance * 5)  # 5x tolerance for fundamentals
    report_parts.append(fund_report)
    report_parts.append("")

    report_parts.append("=" * 60)
    report_parts.append("END OF REPORT")
    report_parts.append("=" * 60)

    return "\n".join(report_parts)
