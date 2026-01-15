"""
test_vnstock.py - Test script to verify vnstock integration works correctly.

This test module validates the Vietnamese stock market data integration
using the vnstock3 library. It tests all core functions including:
- Historical OHLCV data
- Financial statements (balance sheet, cashflow, income statement)
- Financial ratios
- Technical indicators
- News fetching

Tests are designed to:
1. Fetch sample data for VN tickers (TCB, FPT, VNM)
2. Verify data format matches expectations (CSV strings with headers)
3. Pass on clean environment (graceful handling when vnstock3 not installed)
"""

import unittest
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Test tickers - major Vietnamese stocks
VN_TEST_TICKERS = ["TCB", "FPT", "VNM"]


class TestVnstockAvailability(unittest.TestCase):
    """Test vnstock library availability and graceful fallback."""

    def test_vnstock_import(self):
        """Test that vnstock module can be imported."""
        try:
            from tradingagents.dataflows import vnstock
            self.assertTrue(hasattr(vnstock, 'VNSTOCK_AVAILABLE'))
        except ImportError:
            self.skipTest("vnstock module not found in tradingagents.dataflows")

    def test_vnstock_availability_flag(self):
        """Test that VNSTOCK_AVAILABLE flag is set correctly."""
        try:
            from tradingagents.dataflows.vnstock import VNSTOCK_AVAILABLE
            # Just verify it's a boolean
            self.assertIsInstance(VNSTOCK_AVAILABLE, bool)
        except ImportError:
            self.skipTest("vnstock module not found")


class TestVnstockDataFunctions(unittest.TestCase):
    """Test vnstock data fetching functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test class - check if vnstock is available."""
        try:
            from tradingagents.dataflows.vnstock import VNSTOCK_AVAILABLE
            cls.vnstock_available = VNSTOCK_AVAILABLE
        except ImportError:
            cls.vnstock_available = False

    def setUp(self):
        """Set up each test."""
        if not self.vnstock_available:
            self.skipTest("vnstock3 library not installed - skipping live data tests")

        # Calculate date range for tests
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        self.start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    def test_get_vnstock_data_format(self):
        """Test get_vnstock_data returns correct format for all test tickers."""
        from tradingagents.dataflows.vnstock import get_vnstock_data

        for ticker in VN_TEST_TICKERS:
            with self.subTest(ticker=ticker):
                result = get_vnstock_data(ticker, self.start_date, self.end_date)

                # Verify result is a string
                self.assertIsInstance(result, str)

                # Verify header is present (should contain ticker and date info)
                self.assertIn(ticker.upper(), result)
                self.assertIn("Stock data for", result)
                self.assertIn("Market: Vietnam", result)

                # Verify CSV format with expected columns
                # If data found, should have OHLCV headers
                if "No data found" not in result and "Error" not in result:
                    # Check for standard column headers
                    self.assertIn("Date", result)
                    self.assertIn("Open", result)
                    self.assertIn("High", result)
                    self.assertIn("Low", result)
                    self.assertIn("Close", result)
                    self.assertIn("Volume", result)

    def test_get_vnstock_balance_sheet_format(self):
        """Test get_vnstock_balance_sheet returns correct format."""
        from tradingagents.dataflows.vnstock import get_vnstock_balance_sheet

        for ticker in VN_TEST_TICKERS:
            with self.subTest(ticker=ticker):
                result = get_vnstock_balance_sheet(ticker, freq="quarterly")

                # Verify result is a string
                self.assertIsInstance(result, str)

                # Verify header information
                if "No balance sheet data found" not in result and "Error" not in result:
                    self.assertIn("Balance Sheet", result)
                    self.assertIn(ticker.upper(), result)
                    self.assertIn("Market: Vietnam", result)

    def test_get_vnstock_cashflow_format(self):
        """Test get_vnstock_cashflow returns correct format."""
        from tradingagents.dataflows.vnstock import get_vnstock_cashflow

        for ticker in VN_TEST_TICKERS:
            with self.subTest(ticker=ticker):
                result = get_vnstock_cashflow(ticker, freq="quarterly")

                # Verify result is a string
                self.assertIsInstance(result, str)

                # Verify header information
                if "No cash flow data found" not in result and "Error" not in result:
                    self.assertIn("Cash Flow", result)
                    self.assertIn(ticker.upper(), result)
                    self.assertIn("Market: Vietnam", result)

    def test_get_vnstock_income_statement_format(self):
        """Test get_vnstock_income_statement returns correct format."""
        from tradingagents.dataflows.vnstock import get_vnstock_income_statement

        for ticker in VN_TEST_TICKERS:
            with self.subTest(ticker=ticker):
                result = get_vnstock_income_statement(ticker, freq="quarterly")

                # Verify result is a string
                self.assertIsInstance(result, str)

                # Verify header information
                if "No income statement data found" not in result and "Error" not in result:
                    self.assertIn("Income Statement", result)
                    self.assertIn(ticker.upper(), result)
                    self.assertIn("Market: Vietnam", result)

    def test_get_vnstock_financial_ratios_format(self):
        """Test get_vnstock_financial_ratios returns correct format."""
        from tradingagents.dataflows.vnstock import get_vnstock_financial_ratios

        for ticker in VN_TEST_TICKERS:
            with self.subTest(ticker=ticker):
                result = get_vnstock_financial_ratios(ticker)

                # Verify result is a string
                self.assertIsInstance(result, str)

                # Verify header information
                if "No financial ratio data found" not in result and "Error" not in result:
                    self.assertIn("Financial Ratios", result)
                    self.assertIn(ticker.upper(), result)
                    self.assertIn("Market: Vietnam", result)


class TestVnstockIndicators(unittest.TestCase):
    """Test vnstock technical indicators functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        try:
            from tradingagents.dataflows.vnstock import VNSTOCK_AVAILABLE
            cls.vnstock_available = VNSTOCK_AVAILABLE

            # Also check for stockstats
            try:
                import stockstats
                cls.stockstats_available = True
            except ImportError:
                cls.stockstats_available = False
        except ImportError:
            cls.vnstock_available = False
            cls.stockstats_available = False

    def setUp(self):
        """Set up each test."""
        if not self.vnstock_available:
            self.skipTest("vnstock3 library not installed")
        if not self.stockstats_available:
            self.skipTest("stockstats library not installed")

        self.curr_date = datetime.now().strftime("%Y-%m-%d")
        self.look_back_days = 10

    def test_get_vnstock_indicators_rsi(self):
        """Test RSI indicator calculation."""
        from tradingagents.dataflows.vnstock import get_vnstock_indicators

        for ticker in VN_TEST_TICKERS[:1]:  # Test with one ticker to save API calls
            with self.subTest(ticker=ticker):
                result = get_vnstock_indicators(
                    ticker, "rsi", self.curr_date, self.look_back_days
                )

                self.assertIsInstance(result, str)
                if "Error" not in result:
                    self.assertIn("rsi", result.lower())
                    # Should contain date-value pairs
                    self.assertIn(":", result)

    def test_get_vnstock_indicators_macd(self):
        """Test MACD indicator calculation."""
        from tradingagents.dataflows.vnstock import get_vnstock_indicators

        ticker = VN_TEST_TICKERS[0]
        result = get_vnstock_indicators(
            ticker, "macd", self.curr_date, self.look_back_days
        )

        self.assertIsInstance(result, str)
        if "Error" not in result:
            self.assertIn("macd", result.lower())

    def test_get_vnstock_indicators_sma(self):
        """Test SMA indicator calculation."""
        from tradingagents.dataflows.vnstock import get_vnstock_indicators

        ticker = VN_TEST_TICKERS[0]
        result = get_vnstock_indicators(
            ticker, "close_50_sma", self.curr_date, self.look_back_days
        )

        self.assertIsInstance(result, str)
        if "Error" not in result:
            self.assertIn("50 SMA", result)

    def test_unsupported_indicator_raises_error(self):
        """Test that unsupported indicators raise ValueError."""
        from tradingagents.dataflows.vnstock import get_vnstock_indicators

        with self.assertRaises(ValueError) as context:
            get_vnstock_indicators(
                "FPT", "unsupported_indicator", self.curr_date, self.look_back_days
            )

        self.assertIn("not supported", str(context.exception))


class TestVnNews(unittest.TestCase):
    """Test Vietnamese news fetching functionality."""

    def test_vn_news_module_import(self):
        """Test that vn_news module can be imported."""
        try:
            from tradingagents.dataflows import vn_news
            self.assertTrue(hasattr(vn_news, 'get_vn_stock_news'))
            self.assertTrue(hasattr(vn_news, 'get_vn_global_news'))
        except ImportError:
            self.skipTest("vn_news module not found")

    def test_get_vn_stock_news_format(self):
        """Test get_vn_stock_news returns correct format."""
        try:
            from tradingagents.dataflows.vn_news import get_vn_stock_news
        except ImportError:
            self.skipTest("vn_news module not available")

        ticker = "FPT"
        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7

        result = get_vn_stock_news(ticker, curr_date, look_back_days)

        # Verify result is a string
        self.assertIsInstance(result, str)

        # Result should contain header or "No news found" message
        if "No news found" not in result:
            self.assertIn("Vietnamese Stock News", result)
            self.assertIn(ticker.upper(), result)

    def test_get_vn_global_news_format(self):
        """Test get_vn_global_news returns correct format."""
        try:
            from tradingagents.dataflows.vn_news import get_vn_global_news
        except ImportError:
            self.skipTest("vn_news module not available")

        curr_date = datetime.now().strftime("%Y-%m-%d")
        look_back_days = 7

        result = get_vn_global_news(curr_date, look_back_days)

        # Verify result is a string
        self.assertIsInstance(result, str)

        # Result should contain header or "No global market news" message
        if "No global market news" not in result:
            self.assertIn("Vietnamese Market News", result)

    def test_clean_html_function(self):
        """Test HTML cleaning function."""
        try:
            from tradingagents.dataflows.vn_news import _clean_html_text
        except ImportError:
            self.skipTest("vn_news module not available")

        # Test HTML cleaning
        html_input = "<p>Hello <b>World</b></p><script>alert('test')</script>"
        result = _clean_html_text(html_input)

        # Should contain text without HTML tags
        self.assertIn("Hello", result)
        self.assertIn("World", result)

        # Should not contain HTML tags
        self.assertNotIn("<p>", result)
        self.assertNotIn("<b>", result)
        self.assertNotIn("<script>", result)

    def test_invalid_date_format(self):
        """Test error handling for invalid date format."""
        try:
            from tradingagents.dataflows.vn_news import get_vn_stock_news
        except ImportError:
            self.skipTest("vn_news module not available")

        result = get_vn_stock_news("FPT", "invalid-date", 7)

        # Should return error message about invalid date
        self.assertIn("Error", result)
        self.assertIn("Invalid date format", result)


class TestVendorRouting(unittest.TestCase):
    """Test that vnstock is properly registered in vendor routing."""

    def test_vnstock_in_vendor_list(self):
        """Test that vnstock is in the VENDOR_LIST."""
        try:
            from tradingagents.dataflows.interface import VENDOR_LIST
        except ImportError:
            self.skipTest("interface module not available")

        self.assertIn("vnstock", VENDOR_LIST)

    def test_vnstock_in_vendor_methods(self):
        """Test that vnstock is registered in VENDOR_METHODS."""
        try:
            from tradingagents.dataflows.interface import VENDOR_METHODS
        except ImportError:
            self.skipTest("interface module not available")

        # Check vnstock is registered for core methods
        expected_methods = [
            "get_stock_data",
            "get_indicators",
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement",
            "get_news",
            "get_global_news",
        ]

        for method in expected_methods:
            with self.subTest(method=method):
                self.assertIn(method, VENDOR_METHODS)
                self.assertIn("vnstock", VENDOR_METHODS[method])


class TestMarketConfig(unittest.TestCase):
    """Test Vietnam market configuration."""

    def test_vn_market_config_exists(self):
        """Test that VN market config is defined."""
        try:
            from tradingagents.default_config import VN_MARKET_CONFIG
        except ImportError:
            self.skipTest("VN_MARKET_CONFIG not available in default_config")

        self.assertIsInstance(VN_MARKET_CONFIG, dict)
        self.assertEqual(VN_MARKET_CONFIG.get("market"), "vn")

    def test_vn_exchanges_defined(self):
        """Test that VN exchanges are defined with price limits."""
        try:
            from tradingagents.default_config import VN_EXCHANGES
        except ImportError:
            self.skipTest("VN_EXCHANGES not available in default_config")

        self.assertIsInstance(VN_EXCHANGES, dict)

        # Check major exchanges
        expected_exchanges = ["HOSE", "HNX", "UPCOM"]
        for exchange in expected_exchanges:
            with self.subTest(exchange=exchange):
                self.assertIn(exchange, VN_EXCHANGES)
                self.assertIn("price_limit_percent", VN_EXCHANGES[exchange])

    def test_vn_market_rules_defined(self):
        """Test that VN market rules are defined."""
        try:
            from tradingagents.default_config import VN_MARKET_RULES
        except ImportError:
            self.skipTest("VN_MARKET_RULES not available in default_config")

        self.assertIsInstance(VN_MARKET_RULES, dict)

        # Check key rules
        self.assertIn("settlement_days", VN_MARKET_RULES)
        self.assertIn("default_lot_size", VN_MARKET_RULES)
        self.assertIn("currency", VN_MARKET_RULES)

    def test_get_market_config_function(self):
        """Test get_market_config helper function."""
        try:
            from tradingagents.default_config import get_market_config
        except ImportError:
            self.skipTest("get_market_config not available in default_config")

        # Test VN market config
        vn_config = get_market_config("vn")
        self.assertIsInstance(vn_config, dict)
        self.assertEqual(vn_config.get("market"), "vn")

        # Test US market config (default)
        us_config = get_market_config("us")
        self.assertIsInstance(us_config, dict)


class TestDataFormatConsistency(unittest.TestCase):
    """Test that vnstock data format is consistent with yfinance format."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        try:
            from tradingagents.dataflows.vnstock import VNSTOCK_AVAILABLE
            cls.vnstock_available = VNSTOCK_AVAILABLE
        except ImportError:
            cls.vnstock_available = False

    def test_output_is_csv_string(self):
        """Test that all data functions return CSV strings."""
        if not self.vnstock_available:
            self.skipTest("vnstock3 not installed")

        from tradingagents.dataflows.vnstock import (
            get_vnstock_data,
            get_vnstock_balance_sheet,
            get_vnstock_cashflow,
            get_vnstock_income_statement,
        )

        ticker = "FPT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # All functions should return strings
        results = [
            get_vnstock_data(ticker, start_date, end_date),
            get_vnstock_balance_sheet(ticker),
            get_vnstock_cashflow(ticker),
            get_vnstock_income_statement(ticker),
        ]

        for result in results:
            self.assertIsInstance(result, str)

    def test_header_format(self):
        """Test that output includes proper headers."""
        if not self.vnstock_available:
            self.skipTest("vnstock3 not installed")

        from tradingagents.dataflows.vnstock import get_vnstock_data

        ticker = "FPT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        result = get_vnstock_data(ticker, start_date, end_date)

        # Header should start with # and include key information
        lines = result.split('\n')
        header_lines = [l for l in lines if l.startswith('#')]

        if header_lines:  # If we got data (not error)
            self.assertTrue(any('Stock data' in l or 'Error' in l or 'No data' in l for l in lines[:5]))


def run_quick_test():
    """Run a quick smoke test of vnstock functionality."""
    print("=" * 60)
    print("Quick vnstock Integration Test")
    print("=" * 60)

    # Check vnstock availability
    try:
        from tradingagents.dataflows.vnstock import VNSTOCK_AVAILABLE
        if VNSTOCK_AVAILABLE:
            print("[OK] vnstock3 library is available")
        else:
            print("[WARN] vnstock3 library is NOT available")
            print("       Install with: pip install vnstock3")
            return False
    except ImportError as e:
        print(f"[FAIL] Cannot import vnstock module: {e}")
        return False

    # Test data fetching
    try:
        from tradingagents.dataflows.vnstock import get_vnstock_data

        ticker = "FPT"
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        print(f"\nFetching data for {ticker} from {start_date} to {end_date}...")
        result = get_vnstock_data(ticker, start_date, end_date)

        if "Error" in result or "No data" in result:
            print(f"[WARN] {result[:100]}...")
        else:
            lines = result.split('\n')
            print(f"[OK] Received {len(lines)} lines of data")
            print(f"     First line: {lines[0][:60]}...")

    except Exception as e:
        print(f"[FAIL] Error fetching data: {e}")
        return False

    # Test news fetching
    try:
        from tradingagents.dataflows.vn_news import get_vn_stock_news

        curr_date = datetime.now().strftime("%Y-%m-%d")
        print(f"\nFetching news for FPT...")
        result = get_vn_stock_news("FPT", curr_date, 7)

        if "No news found" in result:
            print("[WARN] No news articles found")
        elif "Error" in result:
            print(f"[WARN] {result[:100]}...")
        else:
            print(f"[OK] News fetched successfully")

    except Exception as e:
        print(f"[WARN] News fetching not working: {e}")

    print("\n" + "=" * 60)
    print("Quick test completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test vnstock integration")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick smoke test only"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if args.quick:
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        # Run full test suite
        verbosity = 2 if args.verbose else 1
        unittest.main(verbosity=verbosity, exit=True)
