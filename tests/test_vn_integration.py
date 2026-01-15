"""
test_vn_integration.py - Integration tests for Vietnam market flow.

This module provides comprehensive integration tests for the complete Vietnam
stock market flow including:
- End-to-end tests with Vietnamese tickers
- Market rules validation (T+2.5 settlement, lot size, price limits)
- Agent prompt verification for Vietnam context
- Configuration and vendor routing tests

Tests are designed to:
1. Run in CI environment without requiring external API access
2. Mock external dependencies when needed
3. Verify all Vietnam market components work together correctly
4. Gracefully skip tests when dependencies are not available
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import importlib


# Check for optional dependencies
def check_import(module_path: str) -> bool:
    """Check if a module can be imported without triggering side effects."""
    try:
        parts = module_path.split('.')
        # Try to import the top-level package first
        mod = importlib.import_module(parts[0])
        # Then traverse to the submodule if needed
        for part in parts[1:]:
            mod = getattr(mod, part, None)
            if mod is None:
                return False
        return True
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False


# Check for langchain availability (needed for agent tests)
LANGCHAIN_AVAILABLE = check_import('langchain_core')


# Test tickers for Vietnam market
VN_TEST_TICKERS = {
    "HOSE": ["VNM", "FPT", "TCB", "VCB", "VIC"],
    "HNX": ["SHB", "PVS", "CEO", "MBS"],
    "UPCOM": ["BSR", "OIL", "ACV"],
}


class TestVietnamMarketConfiguration(unittest.TestCase):
    """Test Vietnam market configuration integration."""

    def test_default_config_has_market_field(self):
        """Test that DEFAULT_CONFIG includes market field."""
        from tradingagents.default_config import DEFAULT_CONFIG

        self.assertIn("market", DEFAULT_CONFIG)
        self.assertEqual(DEFAULT_CONFIG["market"], "us")  # Default is US

    def test_vn_market_config_preset(self):
        """Test VN_MARKET_CONFIG preset is properly defined."""
        from tradingagents.default_config import VN_MARKET_CONFIG

        self.assertEqual(VN_MARKET_CONFIG["market"], "vn")
        self.assertIn("data_vendors", VN_MARKET_CONFIG)

        # Verify all data vendors are set to vnstock
        for category, vendor in VN_MARKET_CONFIG["data_vendors"].items():
            self.assertEqual(vendor, "vnstock",
                           f"Vendor for {category} should be vnstock")

    def test_get_market_config_for_vn(self):
        """Test get_market_config returns correct VN configuration."""
        from tradingagents.default_config import get_market_config

        vn_config = get_market_config("vn")

        self.assertEqual(vn_config["market"], "vn")
        self.assertEqual(vn_config["data_vendors"]["core_stock_apis"], "vnstock")
        self.assertEqual(vn_config["data_vendors"]["news_data"], "vnstock")

    def test_vn_exchanges_configuration(self):
        """Test VN_EXCHANGES has all required exchanges."""
        from tradingagents.default_config import VN_EXCHANGES

        expected_exchanges = ["HOSE", "HNX", "UPCOM"]
        for exchange in expected_exchanges:
            self.assertIn(exchange, VN_EXCHANGES)
            self.assertIn("price_limit_percent", VN_EXCHANGES[exchange])
            self.assertIn("lot_size", VN_EXCHANGES[exchange])

        # Verify specific price limits
        self.assertEqual(VN_EXCHANGES["HOSE"]["price_limit_percent"], 7.0)
        self.assertEqual(VN_EXCHANGES["HNX"]["price_limit_percent"], 10.0)
        self.assertEqual(VN_EXCHANGES["UPCOM"]["price_limit_percent"], 15.0)

    def test_vn_market_rules_configuration(self):
        """Test VN_MARKET_RULES has all required rules."""
        from tradingagents.default_config import VN_MARKET_RULES

        self.assertEqual(VN_MARKET_RULES["settlement_days"], 2.5)
        self.assertEqual(VN_MARKET_RULES["default_lot_size"], 100)
        self.assertEqual(VN_MARKET_RULES["currency"], "VND")


class TestVietnamMarketRulesIntegration(unittest.TestCase):
    """Integration tests for Vietnam market trading rules."""

    def setUp(self):
        """Set up test fixtures."""
        try:
            from tradingagents.rules.vn_market_rules import VNMarketRules
            self.rules = VNMarketRules()
        except ImportError:
            self.skipTest("VNMarketRules not available")

    def test_t25_settlement_rule(self):
        """Test T+2.5 settlement validation."""
        # Purchase on Monday
        purchase_date = datetime(2024, 1, 15)  # Monday

        # Cannot sell on Tuesday (T+1)
        sell_date_t1 = datetime(2024, 1, 16)
        is_valid, msg = self.rules.validate_settlement("VNM", purchase_date, sell_date_t1)
        self.assertFalse(is_valid, "Should not allow selling on T+1")
        self.assertIn("T+2.5", msg)

        # Cannot sell on Wednesday (T+2)
        sell_date_t2 = datetime(2024, 1, 17)
        is_valid, msg = self.rules.validate_settlement("VNM", purchase_date, sell_date_t2)
        self.assertFalse(is_valid, "Should not allow selling on T+2")

        # Can sell on Thursday (T+3)
        sell_date_t3 = datetime(2024, 1, 18)
        is_valid, msg = self.rules.validate_settlement("VNM", purchase_date, sell_date_t3)
        self.assertTrue(is_valid, "Should allow selling on T+3")
        self.assertIsNone(msg)

    def test_lot_size_validation(self):
        """Test lot size rounding and validation."""
        # Valid lot size
        is_valid, msg, corrected = self.rules.validate_lot_size(100)
        self.assertTrue(is_valid)
        self.assertEqual(corrected, 100)

        # Invalid lot size - should round down
        is_valid, msg, corrected = self.rules.validate_lot_size(150)
        self.assertFalse(is_valid)
        self.assertEqual(corrected, 100)

        # Large invalid lot size
        is_valid, msg, corrected = self.rules.validate_lot_size(999)
        self.assertFalse(is_valid)
        self.assertEqual(corrected, 900)

        # Below minimum
        is_valid, msg, corrected = self.rules.validate_lot_size(50)
        self.assertFalse(is_valid)
        self.assertEqual(corrected, 0)

    def test_price_limit_validation_by_exchange(self):
        """Test price limit validation for different exchanges."""
        reference_price = 100000  # 100,000 VND

        # Test HOSE ±7%
        ticker_hose = "VNM"
        is_valid, msg, limits = self.rules.validate_price_limit(
            ticker_hose, 95000, reference_price
        )
        self.assertTrue(is_valid, "95,000 should be within HOSE ±7% limit")

        is_valid, msg, limits = self.rules.validate_price_limit(
            ticker_hose, 92000, reference_price
        )
        self.assertFalse(is_valid, "92,000 should be below HOSE floor (93,000)")

        # Test HNX ±10%
        ticker_hnx = "SHB"
        is_valid, msg, limits = self.rules.validate_price_limit(
            ticker_hnx, 91000, reference_price
        )
        self.assertTrue(is_valid, "91,000 should be within HNX ±10% limit")

        # Test UPCOM ±15%
        ticker_upcom = "BSR"
        is_valid, msg, limits = self.rules.validate_price_limit(
            ticker_upcom, 86000, reference_price
        )
        self.assertTrue(is_valid, "86,000 should be within UPCOM ±15% limit")

    def test_exchange_detection(self):
        """Test exchange detection for known tickers."""
        # HOSE tickers
        for ticker in VN_TEST_TICKERS["HOSE"]:
            exchange = self.rules.get_exchange(ticker)
            self.assertEqual(exchange, "HOSE", f"{ticker} should be HOSE")

        # HNX tickers
        for ticker in VN_TEST_TICKERS["HNX"]:
            exchange = self.rules.get_exchange(ticker)
            self.assertEqual(exchange, "HNX", f"{ticker} should be HNX")

        # UPCOM tickers
        for ticker in VN_TEST_TICKERS["UPCOM"]:
            exchange = self.rules.get_exchange(ticker)
            self.assertEqual(exchange, "UPCOM", f"{ticker} should be UPCOM")

    def test_comprehensive_trade_validation(self):
        """Test validate_trade with all rules."""
        # Valid buy order
        result = self.rules.validate_trade(
            ticker="VNM",
            action="buy",
            quantity=100,
            price=95000,
            reference_price=100000
        )
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["corrected_quantity"], 100)
        self.assertEqual(len(result["errors"]), 0)

        # Invalid buy - wrong lot size
        result = self.rules.validate_trade(
            ticker="VNM",
            action="buy",
            quantity=150,
            price=95000,
            reference_price=100000
        )
        # Should be valid but with warning
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["corrected_quantity"], 100)
        self.assertGreater(len(result["warnings"]), 0)

        # Invalid buy - price outside limit
        result = self.rules.validate_trade(
            ticker="VNM",
            action="buy",
            quantity=100,
            price=110000,  # +10% - exceeds HOSE ±7%
            reference_price=100000
        )
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_format_rules_summary(self):
        """Test rules summary formatting."""
        summary = self.rules.format_rules_summary()

        # Should contain key rule descriptions
        self.assertIn("T+2.5", summary)
        self.assertIn("100", summary)  # Lot size
        self.assertIn("HOSE", summary)
        self.assertIn("±7%", summary)
        self.assertIn("VND", summary)

        # Test with specific ticker
        summary_with_ticker = self.rules.format_rules_summary(ticker="VNM")
        self.assertIn("HOSE", summary_with_ticker)


@unittest.skipUnless(LANGCHAIN_AVAILABLE, "langchain_core not installed")
class TestVietnamHoldingsTracking(unittest.TestCase):
    """Test Vietnam holdings tracking for T+2.5 settlement."""

    def test_create_vn_holding(self):
        """Test VNHolding creation."""
        from tradingagents.agents.utils.agent_states import (
            create_vn_holding,
        )

        holding = create_vn_holding(
            ticker="VNM",
            quantity=100,
            purchase_date="2024-01-15",
            purchase_price=95000,
            exchange="HOSE"
        )

        self.assertEqual(holding["ticker"], "VNM")
        self.assertEqual(holding["quantity"], 100)
        self.assertEqual(holding["purchase_date"], "2024-01-15")
        self.assertEqual(holding["purchase_price"], 95000)
        self.assertEqual(holding["exchange"], "HOSE")

    def test_can_sell_holding_t25_rule(self):
        """Test can_sell_holding enforces T+2.5."""
        from tradingagents.agents.utils.agent_states import (
            create_vn_holding,
            can_sell_holding,
        )

        holding = create_vn_holding(
            ticker="FPT",
            quantity=100,
            purchase_date="2024-01-15"
        )

        # T+1: Cannot sell
        can_sell, earliest, msg = can_sell_holding(holding, "2024-01-16")
        self.assertFalse(can_sell)
        self.assertEqual(earliest, "2024-01-18")

        # T+2: Cannot sell
        can_sell, earliest, msg = can_sell_holding(holding, "2024-01-17")
        self.assertFalse(can_sell)

        # T+3: Can sell
        can_sell, earliest, msg = can_sell_holding(holding, "2024-01-18")
        self.assertTrue(can_sell)

    def test_get_sellable_holdings(self):
        """Test filtering of sellable holdings."""
        from tradingagents.agents.utils.agent_states import (
            create_vn_holding,
            get_sellable_holdings,
        )

        holdings = [
            create_vn_holding("VNM", 100, "2024-01-15"),  # Sellable on 1/18
            create_vn_holding("FPT", 200, "2024-01-16"),  # Sellable on 1/19
            create_vn_holding("TCB", 300, "2024-01-17"),  # Sellable on 1/20
        ]

        # On 2024-01-18, only VNM is sellable
        sellable, unsellable = get_sellable_holdings(holdings, "2024-01-18")
        self.assertEqual(len(sellable), 1)
        self.assertEqual(sellable[0]["ticker"], "VNM")
        self.assertEqual(len(unsellable), 2)

        # On 2024-01-20, all are sellable
        sellable, unsellable = get_sellable_holdings(holdings, "2024-01-20")
        self.assertEqual(len(sellable), 3)
        self.assertEqual(len(unsellable), 0)

    def test_holdings_summary_formatting(self):
        """Test holdings summary generation."""
        from tradingagents.agents.utils.agent_states import (
            create_vn_holding,
            get_holdings_summary,
        )

        holdings = [
            create_vn_holding("VNM", 100, "2024-01-15", 95000),
            create_vn_holding("VNM", 200, "2024-01-16", 96000),
        ]

        summary = get_holdings_summary(holdings, "2024-01-18")

        self.assertIn("VNM", summary)
        self.assertIn("300 shares total", summary)
        self.assertIn("Sellable", summary)


@unittest.skipUnless(LANGCHAIN_AVAILABLE, "langchain_core not installed")
class TestAgentPromptsVietnamContext(unittest.TestCase):
    """Test that agent prompts use Vietnam context when configured."""

    def test_fundamentals_analyst_vn_prompt(self):
        """Test fundamentals analyst has Vietnam-specific prompt."""
        from tradingagents.agents.analysts.fundamentals_analyst import (
            _get_vn_fundamentals_system_message,
        )

        prompt = _get_vn_fundamentals_system_message()

        # Should contain Vietnam-specific content
        self.assertIn("HOSE", prompt)
        self.assertIn("HNX", prompt)
        self.assertIn("UPCOM", prompt)
        self.assertIn("Vietnamese", prompt)

        # Should contain Vietnamese terminology
        self.assertIn("Báo cáo tài chính", prompt)
        self.assertIn("Ngân hàng", prompt)  # Banking
        self.assertIn("Bất động sản", prompt)  # Real Estate

    def test_market_analyst_vn_prompt(self):
        """Test market analyst has Vietnam-specific prompt."""
        from tradingagents.agents.analysts.market_analyst import (
            _get_vn_market_system_message,
        )

        prompt = _get_vn_market_system_message()

        # Should contain Vietnam market indices
        self.assertIn("VN-Index", prompt)
        self.assertIn("HNX-Index", prompt)

        # Should contain trading hours
        self.assertIn("09:00", prompt)
        self.assertIn("14:45", prompt)

        # Should contain price limits
        self.assertIn("±7%", prompt)
        self.assertIn("±10%", prompt)
        self.assertIn("±15%", prompt)

    def test_news_analyst_vn_prompt(self):
        """Test news analyst has Vietnam-specific prompt."""
        from tradingagents.agents.analysts.news_analyst import (
            _get_vn_news_system_message,
        )

        prompt = _get_vn_news_system_message()

        # Should contain Vietnamese news sources
        self.assertIn("CafeF", prompt)
        self.assertIn("Vietstock", prompt)
        self.assertIn("VnExpress", prompt)

        # Should contain Vietnam economic context
        self.assertIn("VN-Index", prompt)
        self.assertIn("SBV", prompt)  # State Bank of Vietnam

    def test_trader_vn_prompt(self):
        """Test trader has Vietnam-specific prompt."""
        from tradingagents.agents.trader.trader import (
            _get_vn_trader_system_message,
        )

        prompt = _get_vn_trader_system_message()

        # Should contain T+2.5 rule
        self.assertIn("T+2.5", prompt)

        # Should contain lot size info
        self.assertIn("100", prompt)

        # Should contain price limits
        self.assertIn("HOSE", prompt)
        self.assertIn("±7%", prompt)


@unittest.skipUnless(LANGCHAIN_AVAILABLE, "langchain_core not installed")
class TestVendorRoutingVietnam(unittest.TestCase):
    """Test vendor routing for Vietnam market."""

    def test_vnstock_in_vendor_list(self):
        """Test vnstock is registered as a vendor."""
        from tradingagents.dataflows.interface import VENDOR_LIST

        self.assertIn("vnstock", VENDOR_LIST)

    def test_vnstock_methods_registered(self):
        """Test all vnstock methods are registered."""
        from tradingagents.dataflows.interface import VENDOR_METHODS

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
            self.assertIn(method, VENDOR_METHODS)
            self.assertIn("vnstock", VENDOR_METHODS[method],
                         f"vnstock should be registered for {method}")

    @patch('tradingagents.dataflows.config.get_config')
    def test_vendor_routing_with_vn_config(self, mock_get_config):
        """Test vendor routing uses vnstock for VN market config."""
        from tradingagents.dataflows.interface import get_vendor

        # Mock VN market configuration
        mock_get_config.return_value = {
            "market": "vn",
            "data_vendors": {
                "core_stock_apis": "vnstock",
                "technical_indicators": "vnstock",
                "fundamental_data": "vnstock",
                "news_data": "vnstock",
            },
            "tool_vendors": {},
        }

        # Should return vnstock for VN market
        vendor = get_vendor("core_stock_apis")
        self.assertEqual(vendor, "vnstock")

        vendor = get_vendor("news_data")
        self.assertEqual(vendor, "vnstock")


class TestDataCacheIntegration(unittest.TestCase):
    """Test data cache integration for Vietnam data."""

    def setUp(self):
        """Set up test fixtures."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_initialization(self):
        """Test DataCache can be initialized."""
        from tradingagents.dataflows.cache import DataCache

        cache = DataCache(cache_dir=self.temp_dir)
        self.assertIsNotNone(cache)

    def test_cache_set_get(self):
        """Test basic cache operations."""
        from tradingagents.dataflows.cache import DataCache

        cache = DataCache(cache_dir=self.temp_dir)

        # Set a value
        test_data = {"ticker": "VNM", "price": 95000}
        cache.set("test_key", test_data, ttl_seconds=60)

        # Get the value
        retrieved = cache.get("test_key")
        self.assertEqual(retrieved, test_data)

    def test_cache_key_generation(self):
        """Test cache key generation."""
        from tradingagents.dataflows.cache import generate_cache_key

        key = generate_cache_key(
            category="stock_data",
            ticker="VNM",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        self.assertIn("stock_data", key)
        self.assertIn("VNM", key)
        self.assertIn("2024-01-01", key)

    def test_ttl_presets(self):
        """Test TTL presets for different data types."""
        from tradingagents.dataflows.cache import TTL_PRESETS, get_ttl_for_category

        # Check presets exist
        self.assertIn("stock_data", TTL_PRESETS)
        self.assertIn("news", TTL_PRESETS)
        self.assertIn("fundamentals", TTL_PRESETS)

        # Check helper function
        ttl = get_ttl_for_category("news")
        self.assertEqual(ttl, TTL_PRESETS["news"])


class TestEndToEndVietnamFlow(unittest.TestCase):
    """End-to-end integration tests for Vietnam market flow."""

    @patch('tradingagents.dataflows.config._config', None)
    def test_config_flow_vn_market(self):
        """Test configuration flow for VN market."""
        from tradingagents.dataflows.config import set_config, get_config
        from tradingagents.default_config import VN_MARKET_CONFIG, DEFAULT_CONFIG

        # Reset config
        set_config(DEFAULT_CONFIG.copy())

        # Update to VN config
        vn_config = DEFAULT_CONFIG.copy()
        vn_config.update(VN_MARKET_CONFIG)
        set_config(vn_config)

        config = get_config()
        self.assertEqual(config["market"], "vn")

    def test_market_rules_class_integration(self):
        """Test VNMarketRules class with realistic scenario."""
        from tradingagents.rules.vn_market_rules import VNMarketRules

        rules = VNMarketRules()

        # Simulate a trading scenario
        ticker = "FPT"
        purchase_date = datetime(2024, 1, 15)  # Monday

        # Day 1 (T+0): Buy
        buy_result = rules.validate_trade(
            ticker=ticker,
            action="buy",
            quantity=500,
            price=85000,
            reference_price=80000  # Within ±7% limit
        )
        self.assertTrue(buy_result["is_valid"])
        self.assertEqual(buy_result["corrected_quantity"], 500)

        # Day 2 (T+1): Try to sell - should fail
        sell_result_t1 = rules.validate_trade(
            ticker=ticker,
            action="sell",
            quantity=500,
            purchase_date=purchase_date,
            trade_date=datetime(2024, 1, 16)
        )
        self.assertFalse(sell_result_t1["is_valid"])
        self.assertIn("T+2.5", sell_result_t1["errors"][0])

        # Day 4 (T+3): Sell - should succeed
        sell_result_t3 = rules.validate_trade(
            ticker=ticker,
            action="sell",
            quantity=500,
            purchase_date=purchase_date,
            trade_date=datetime(2024, 1, 18)
        )
        self.assertTrue(sell_result_t3["is_valid"])

    @unittest.skipUnless(LANGCHAIN_AVAILABLE, "langchain_core not installed")
    @patch('tradingagents.dataflows.config.get_config')
    def test_analyst_prompt_selection_with_vn_config(self, mock_get_config):
        """Test that analysts select VN prompts when market=vn."""
        mock_get_config.return_value = {"market": "vn"}

        # Test fundamentals analyst
        from tradingagents.agents.analysts.fundamentals_analyst import (
            _get_us_fundamentals_system_message,
            _get_vn_fundamentals_system_message,
        )

        us_prompt = _get_us_fundamentals_system_message()
        vn_prompt = _get_vn_fundamentals_system_message()

        # Prompts should be different
        self.assertNotEqual(us_prompt, vn_prompt)

        # VN prompt should have Vietnamese context
        self.assertIn("Vietnamese", vn_prompt)
        self.assertNotIn("Vietnamese", us_prompt)


class TestDataModulesAvailability(unittest.TestCase):
    """Test that data modules are importable and have required functions."""

    def test_vnstock_module_importable(self):
        """Test vnstock module can be imported."""
        try:
            from tradingagents.dataflows import vnstock
            self.assertTrue(hasattr(vnstock, 'get_vnstock_data'))
            self.assertTrue(hasattr(vnstock, 'get_vnstock_balance_sheet'))
            self.assertTrue(hasattr(vnstock, 'get_vnstock_cashflow'))
            self.assertTrue(hasattr(vnstock, 'get_vnstock_income_statement'))
            self.assertTrue(hasattr(vnstock, 'get_vnstock_financial_ratios'))
            self.assertTrue(hasattr(vnstock, 'get_vnstock_indicators'))
        except ImportError as e:
            self.skipTest(f"vnstock module not available: {e}")

    def test_vn_news_module_importable(self):
        """Test vn_news module can be imported."""
        try:
            from tradingagents.dataflows import vn_news
            self.assertTrue(hasattr(vn_news, 'get_vn_stock_news'))
            self.assertTrue(hasattr(vn_news, 'get_vn_global_news'))
        except ImportError as e:
            self.skipTest(f"vn_news module not available: {e}")

    def test_cache_module_importable(self):
        """Test cache module can be imported."""
        try:
            from tradingagents.dataflows import cache
            self.assertTrue(hasattr(cache, 'DataCache'))
            self.assertTrue(hasattr(cache, 'get_cache'))
            self.assertTrue(hasattr(cache, 'generate_cache_key'))
        except ImportError as e:
            self.skipTest(f"cache module not available: {e}")


class TestVietnamRulesExceptions(unittest.TestCase):
    """Test Vietnam market rules custom exceptions."""

    def test_settlement_error(self):
        """Test SettlementError is raised correctly."""
        from tradingagents.rules.vn_market_rules import (
            validate_settlement,
            SettlementError,
        )

        purchase_date = datetime(2024, 1, 15)
        sell_date = datetime(2024, 1, 16)  # T+1, too early

        with self.assertRaises(SettlementError) as context:
            validate_settlement("VNM", purchase_date, sell_date, raise_error=True)

        self.assertIn("T+2.5", str(context.exception))

    def test_lot_size_error(self):
        """Test LotSizeError is raised correctly."""
        from tradingagents.rules.vn_market_rules import (
            validate_lot_size,
            LotSizeError,
        )

        with self.assertRaises(LotSizeError) as context:
            validate_lot_size(150, raise_error=True)

        self.assertIn("Invalid lot size", str(context.exception))

    def test_price_limit_error(self):
        """Test PriceLimitError is raised correctly."""
        from tradingagents.rules.vn_market_rules import (
            validate_price_limit,
            PriceLimitError,
        )

        with self.assertRaises(PriceLimitError) as context:
            validate_price_limit("VNM", 110000, 100000, raise_error=True)

        self.assertIn("exceeds", str(context.exception))


def run_quick_integration_test():
    """Run a quick smoke test of Vietnam market integration."""
    print("=" * 60)
    print("Quick Vietnam Market Integration Test")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0
    tests_skipped = 0

    # Test 1: Configuration
    try:
        from tradingagents.default_config import (
            VN_MARKET_CONFIG,
            VN_EXCHANGES,
            VN_MARKET_RULES,
        )
        assert VN_MARKET_CONFIG["market"] == "vn"
        assert "HOSE" in VN_EXCHANGES
        assert VN_MARKET_RULES["settlement_days"] == 2.5
        print("[OK] Vietnam configuration loaded correctly")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        tests_failed += 1

    # Test 2: Market Rules
    try:
        from tradingagents.rules.vn_market_rules import VNMarketRules
        rules = VNMarketRules()
        assert rules.round_lot_size(150) == 100
        assert rules.get_exchange("VNM") == "HOSE"
        print("[OK] Market rules working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Market rules test failed: {e}")
        tests_failed += 1

    # Test 3: Holdings Tracking (requires langchain)
    if LANGCHAIN_AVAILABLE:
        try:
            from tradingagents.agents.utils.agent_states import (
                create_vn_holding,
                can_sell_holding,
            )
            holding = create_vn_holding("FPT", 100, "2024-01-15")
            can_sell, _, _ = can_sell_holding(holding, "2024-01-18")
            assert can_sell is True
            print("[OK] Holdings tracking working correctly")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] Holdings tracking test failed: {e}")
            tests_failed += 1
    else:
        print("[SKIP] Holdings tracking (langchain not installed)")
        tests_skipped += 1

    # Test 4: Agent Prompts (requires langchain)
    if LANGCHAIN_AVAILABLE:
        try:
            from tradingagents.agents.analysts.fundamentals_analyst import (
                _get_vn_fundamentals_system_message,
            )
            prompt = _get_vn_fundamentals_system_message()
            assert "Vietnamese" in prompt
            assert "HOSE" in prompt
            print("[OK] Vietnam agent prompts available")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] Agent prompts test failed: {e}")
            tests_failed += 1
    else:
        print("[SKIP] Agent prompts (langchain not installed)")
        tests_skipped += 1

    # Test 5: Vendor Routing (requires langchain for interface.py imports)
    if LANGCHAIN_AVAILABLE:
        try:
            from tradingagents.dataflows.interface import VENDOR_LIST, VENDOR_METHODS
            assert "vnstock" in VENDOR_LIST
            assert "vnstock" in VENDOR_METHODS["get_stock_data"]
            print("[OK] Vnstock vendor registered correctly")
            tests_passed += 1
        except Exception as e:
            print(f"[FAIL] Vendor routing test failed: {e}")
            tests_failed += 1
    else:
        print("[SKIP] Vendor routing (langchain not installed)")
        tests_skipped += 1

    # Test 6: Data Cache
    try:
        import tempfile
        from tradingagents.dataflows.cache import DataCache
        temp_dir = tempfile.mkdtemp()
        cache = DataCache(cache_dir=temp_dir)
        cache.set("test", {"data": "value"}, ttl_seconds=60)
        assert cache.get("test") == {"data": "value"}
        print("[OK] Data cache working correctly")
        tests_passed += 1
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print(f"[FAIL] Data cache test failed: {e}")
        tests_failed += 1

    print()
    print("=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed, {tests_skipped} skipped")
    print("=" * 60)

    return tests_failed == 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vietnam market integration tests")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick smoke test only"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    if args.quick:
        success = run_quick_integration_test()
        sys.exit(0 if success else 1)
    else:
        # Run full test suite
        verbosity = 2 if args.verbose else 1
        unittest.main(verbosity=verbosity, exit=True)
