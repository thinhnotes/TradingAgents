"""
vn_market_rules.py - Vietnam stock market trading rules and validation.

This module provides trading rules and validation functions for the Vietnamese
stock market including:
- T+2.5 settlement rule (can sell morning of T+3)
- Lot size rounding (multiples of 100)
- Price limit validation (HOSE ±7%, HNX ±10%, UPCOM ±15%)
- Exchange detection for Vietnamese tickers

Supported exchanges: HOSE, HNX, UPCOM
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import math


# ============================================================================
# Custom Exceptions
# ============================================================================


class SettlementError(Exception):
    """Raised when a trade violates the T+2.5 settlement rule."""
    pass


class LotSizeError(Exception):
    """Raised when an order quantity is not a valid lot size."""
    pass


class PriceLimitError(Exception):
    """Raised when a price exceeds the daily price limit."""
    pass


# ============================================================================
# Exchange Configuration
# ============================================================================

# Vietnam exchange definitions with price limits and lot sizes
VN_EXCHANGES = {
    "HOSE": {
        "name": "Ho Chi Minh Stock Exchange",
        "price_limit_percent": 7.0,    # ±7% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
    "HNX": {
        "name": "Hanoi Stock Exchange",
        "price_limit_percent": 10.0,   # ±10% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
    "UPCOM": {
        "name": "Unlisted Public Company Market",
        "price_limit_percent": 15.0,   # ±15% daily price limit
        "lot_size": 100,               # Minimum lot size
        "trading_hours": "09:00-11:30, 13:00-15:00",
        "timezone": "Asia/Ho_Chi_Minh",
    },
}

# T+2.5 settlement: Stocks bought on day T can be sold on morning of T+3
# This means 2 full business days + morning of 3rd day = 2.5 days
SETTLEMENT_DAYS = 2.5

# Default lot size for all Vietnam exchanges
DEFAULT_LOT_SIZE = 100


# ============================================================================
# Exchange Detection
# ============================================================================

# Known ticker mappings to exchanges
# This is a sample list - in production, this would be fetched from an API
# or database. The format is ticker: exchange
TICKER_EXCHANGE_MAP = {
    # HOSE (Ho Chi Minh Stock Exchange) - Major companies
    "VNM": "HOSE",  # Vinamilk
    "VIC": "HOSE",  # Vingroup
    "VHM": "HOSE",  # Vinhomes
    "HPG": "HOSE",  # Hoa Phat Group
    "FPT": "HOSE",  # FPT Corporation
    "MWG": "HOSE",  # Mobile World Group
    "VCB": "HOSE",  # Vietcombank
    "BID": "HOSE",  # BIDV
    "CTG": "HOSE",  # VietinBank
    "TCB": "HOSE",  # Techcombank
    "VPB": "HOSE",  # VP Bank
    "MBB": "HOSE",  # Military Bank
    "ACB": "HOSE",  # Asia Commercial Bank
    "STB": "HOSE",  # Sacombank
    "HDB": "HOSE",  # HDBank
    "TPB": "HOSE",  # TPBank
    "SSI": "HOSE",  # SSI Securities
    "VND": "HOSE",  # VNDirect Securities
    "VRE": "HOSE",  # Vincom Retail
    "PLX": "HOSE",  # Petrolimex
    "GAS": "HOSE",  # PetroVietnam Gas
    "POW": "HOSE",  # PetroVietnam Power
    "VGC": "HOSE",  # Viglacera
    "REE": "HOSE",  # REE Corporation
    "SAB": "HOSE",  # Sabeco
    "MSN": "HOSE",  # Masan Group
    "GMD": "HOSE",  # Gemadept
    "GVR": "HOSE",  # Vietnam Rubber Group
    "DPM": "HOSE",  # PetroVietnam Fertilizer
    "DCM": "HOSE",  # Dinh Vu - Cat Hai Fertilizer
    "PNJ": "HOSE",  # Phu Nhuan Jewelry
    "DGC": "HOSE",  # Duc Giang Chemical
    "NVL": "HOSE",  # Novaland
    "KDH": "HOSE",  # Khang Dien House
    "SBT": "HOSE",  # TTC Sugar
    "HAG": "HOSE",  # Hoang Anh Gia Lai
    "HNG": "HOSE",  # HAGL Agrico
    "EIB": "HOSE",  # Eximbank
    "LPB": "HOSE",  # Lien Viet Post Bank
    "OCB": "HOSE",  # Orient Commercial Bank
    "SSB": "HOSE",  # SeABank
    "VIB": "HOSE",  # Vietnam International Bank
    "HCM": "HOSE",  # HSC Securities
    "VCI": "HOSE",  # Viet Capital Securities
    "SHS": "HOSE",  # SHB Securities
    "DIG": "HOSE",  # DIC Group
    "BCM": "HOSE",  # Becamex IDC
    "HSG": "HOSE",  # Hoa Sen Group
    "PHR": "HOSE",  # Phu Rieng Rubber

    # HNX (Hanoi Stock Exchange)
    "SHB": "HNX",   # Saigon-Hanoi Bank
    "PVS": "HNX",   # PetroVietnam Services
    "CEO": "HNX",   # CE O Group
    "IDC": "HNX",   # IDICO
    "THD": "HNX",   # ThaiDuong Group
    "NVB": "HNX",   # Nam Viet Bank
    "DTD": "HNX",   # Dat Thanh
    "PVI": "HNX",   # PVI Holdings
    "VGS": "HNX",   # Vietnam General Trading
    "BVS": "HNX",   # Bao Viet Securities
    "MBS": "HNX",   # MB Securities
    "TVS": "HNX",   # Thien Viet Securities
    "APS": "HNX",   # Asia Pacific Securities
    "HUT": "HNX",   # Hud Urban Development
    "LHG": "HNX",   # Long Hau Corp
    "NDN": "HNX",   # Danang Housing

    # UPCOM (Unlisted Public Company Market) - OTC market
    "BSR": "UPCOM",  # Binh Son Refining
    "OIL": "UPCOM",  # PetroVietnam Oil
    "ACV": "UPCOM",  # Airports Corp
    "VEA": "UPCOM",  # Vietnam Engine
    "VGT": "UPCOM",  # Vietnam Textile
    "MCH": "UPCOM",  # Masan Consumer Holdings
    "QNS": "UPCOM",  # QNS Corp
    "FOX": "UPCOM",  # FPT Online
}


def get_exchange_for_ticker(ticker: str) -> str:
    """
    Determine the exchange for a Vietnamese stock ticker.

    Args:
        ticker: Vietnamese stock ticker symbol (e.g., 'VNM', 'FPT', 'SHB')

    Returns:
        Exchange code: 'HOSE', 'HNX', or 'UPCOM'
        Defaults to 'HOSE' if ticker is not found in mapping.

    Note:
        This function uses a static mapping. For production use, consider
        integrating with vnstock3 API to get real-time exchange information.
    """
    ticker_upper = ticker.upper().strip()
    return TICKER_EXCHANGE_MAP.get(ticker_upper, "HOSE")


# ============================================================================
# Settlement Validation (T+2.5 Rule)
# ============================================================================


def validate_settlement(
    ticker: str,
    purchase_date: datetime,
    sell_date: datetime,
    raise_error: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Validate if a stock can be sold based on T+2.5 settlement rule.

    In Vietnam, stocks bought on day T can only be sold from the morning
    of T+3 (2.5 business days later). This function checks if the proposed
    sell date is valid.

    Args:
        ticker: Stock ticker symbol
        purchase_date: Date when the stock was purchased
        sell_date: Proposed date to sell the stock
        raise_error: If True, raise SettlementError when invalid

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])

    Raises:
        SettlementError: If raise_error=True and sell is not allowed

    Example:
        >>> from datetime import datetime
        >>> purchase = datetime(2024, 1, 15)  # Monday
        >>> sell = datetime(2024, 1, 17)  # Wednesday
        >>> is_valid, msg = validate_settlement("VNM", purchase, sell)
        >>> print(is_valid)
        False
        >>> print(msg)
        "Cannot sell VNM: Stock purchased on 2024-01-15 cannot be sold until 2024-01-18 (T+2.5 rule)"
    """
    # Calculate earliest sell date: T+3 (morning of 3rd business day)
    # For simplicity, we use calendar days. In production, consider
    # business days (excluding weekends and holidays)
    earliest_sell_date = purchase_date + timedelta(days=3)

    if sell_date < earliest_sell_date:
        error_msg = (
            f"Cannot sell {ticker.upper()}: Stock purchased on {purchase_date.strftime('%Y-%m-%d')} "
            f"cannot be sold until {earliest_sell_date.strftime('%Y-%m-%d')} (T+2.5 rule)"
        )
        if raise_error:
            raise SettlementError(error_msg)
        return False, error_msg

    return True, None


def get_earliest_sell_date(purchase_date: datetime) -> datetime:
    """
    Get the earliest date a stock can be sold after purchase.

    Based on T+2.5 settlement rule: stocks can be sold from morning of T+3.

    Args:
        purchase_date: Date when the stock was purchased

    Returns:
        Earliest date the stock can be sold
    """
    return purchase_date + timedelta(days=3)


def can_sell_today(purchase_date: datetime, current_date: datetime = None) -> bool:
    """
    Check if a stock purchased on given date can be sold today.

    Args:
        purchase_date: Date when the stock was purchased
        current_date: Current date (defaults to today if not provided)

    Returns:
        True if stock can be sold, False otherwise
    """
    if current_date is None:
        current_date = datetime.now()

    # Remove time component for date comparison
    purchase_date = purchase_date.replace(hour=0, minute=0, second=0, microsecond=0)
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)

    is_valid, _ = validate_settlement("", purchase_date, current_date, raise_error=False)
    return is_valid


# ============================================================================
# Lot Size Validation
# ============================================================================


def round_lot_size(quantity: int, exchange: str = "HOSE") -> int:
    """
    Round order quantity down to the nearest valid lot size.

    In Vietnam, all exchanges require orders in multiples of 100 shares.
    This function rounds down to ensure the order meets the requirement.

    Args:
        quantity: Requested number of shares
        exchange: Exchange code (HOSE, HNX, UPCOM). All use 100-share lots.

    Returns:
        Rounded quantity (always a multiple of lot size)

    Example:
        >>> round_lot_size(150)
        100
        >>> round_lot_size(999)
        900
        >>> round_lot_size(50)
        0
    """
    exchange_info = VN_EXCHANGES.get(exchange.upper(), VN_EXCHANGES["HOSE"])
    lot_size = exchange_info["lot_size"]

    # Round down to nearest lot size
    return (quantity // lot_size) * lot_size


def validate_lot_size(
    quantity: int,
    exchange: str = "HOSE",
    raise_error: bool = True
) -> Tuple[bool, Optional[str], int]:
    """
    Validate if order quantity is a valid lot size.

    Args:
        quantity: Number of shares to trade
        exchange: Exchange code (HOSE, HNX, UPCOM)
        raise_error: If True, raise LotSizeError when invalid

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str], corrected_quantity: int)

    Raises:
        LotSizeError: If raise_error=True and quantity is not valid

    Example:
        >>> is_valid, msg, corrected = validate_lot_size(150)
        >>> print(is_valid, corrected)
        False 100
    """
    exchange_info = VN_EXCHANGES.get(exchange.upper(), VN_EXCHANGES["HOSE"])
    lot_size = exchange_info["lot_size"]

    corrected_quantity = round_lot_size(quantity, exchange)

    if quantity % lot_size != 0:
        error_msg = (
            f"Invalid lot size: {quantity} shares. "
            f"Orders must be in multiples of {lot_size}. "
            f"Rounded down to {corrected_quantity} shares."
        )
        if raise_error:
            raise LotSizeError(error_msg)
        return False, error_msg, corrected_quantity

    if quantity < lot_size:
        error_msg = (
            f"Quantity {quantity} is less than minimum lot size of {lot_size} shares."
        )
        if raise_error:
            raise LotSizeError(error_msg)
        return False, error_msg, 0

    return True, None, quantity


# ============================================================================
# Price Limit Validation
# ============================================================================


def validate_price_limit(
    ticker: str,
    order_price: float,
    reference_price: float,
    exchange: str = None,
    raise_error: bool = True
) -> Tuple[bool, Optional[str], Tuple[float, float]]:
    """
    Validate if order price is within the daily price limit.

    Each Vietnam exchange has different daily price limits:
    - HOSE: ±7% from reference price
    - HNX: ±10% from reference price
    - UPCOM: ±15% from reference price

    Args:
        ticker: Stock ticker symbol
        order_price: Proposed order price
        reference_price: Reference price (previous day's close)
        exchange: Exchange code. If None, determined from ticker.
        raise_error: If True, raise PriceLimitError when invalid

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str], (floor_price, ceiling_price))

    Raises:
        PriceLimitError: If raise_error=True and price is outside limit

    Example:
        >>> is_valid, msg, limits = validate_price_limit("VNM", 95000, 100000)
        >>> print(is_valid)
        True
        >>> print(limits)
        (93000.0, 107000.0)
    """
    if exchange is None:
        exchange = get_exchange_for_ticker(ticker)

    exchange_info = VN_EXCHANGES.get(exchange.upper(), VN_EXCHANGES["HOSE"])
    limit_percent = exchange_info["price_limit_percent"] / 100.0

    # Calculate floor and ceiling prices
    floor_price = reference_price * (1 - limit_percent)
    ceiling_price = reference_price * (1 + limit_percent)

    # Round to appropriate precision (VND typically rounds to 10 or 100)
    floor_price = math.floor(floor_price / 10) * 10
    ceiling_price = math.ceil(ceiling_price / 10) * 10

    if order_price < floor_price:
        error_msg = (
            f"Price {order_price:,.0f} VND is below floor price {floor_price:,.0f} VND "
            f"(-{exchange_info['price_limit_percent']}% limit for {exchange.upper()})"
        )
        if raise_error:
            raise PriceLimitError(error_msg)
        return False, error_msg, (floor_price, ceiling_price)

    if order_price > ceiling_price:
        error_msg = (
            f"Price {order_price:,.0f} VND exceeds ceiling price {ceiling_price:,.0f} VND "
            f"(+{exchange_info['price_limit_percent']}% limit for {exchange.upper()})"
        )
        if raise_error:
            raise PriceLimitError(error_msg)
        return False, error_msg, (floor_price, ceiling_price)

    return True, None, (floor_price, ceiling_price)


def get_price_limits(
    ticker: str,
    reference_price: float,
    exchange: str = None
) -> Tuple[float, float]:
    """
    Get floor and ceiling prices for a ticker.

    Args:
        ticker: Stock ticker symbol
        reference_price: Reference price (previous day's close)
        exchange: Exchange code. If None, determined from ticker.

    Returns:
        Tuple of (floor_price, ceiling_price)
    """
    _, _, limits = validate_price_limit(
        ticker, reference_price, reference_price, exchange, raise_error=False
    )
    return limits


# ============================================================================
# VNMarketRules Class
# ============================================================================


class VNMarketRules:
    """
    Vietnam stock market trading rules validator.

    This class encapsulates all Vietnam-specific trading rules and provides
    a unified interface for validating trades. It can be used by the
    RiskManagementAgent to enforce market rules.

    Attributes:
        exchanges: Dictionary of exchange configurations
        settlement_days: T+2.5 settlement period
        default_lot_size: Default lot size (100 shares)

    Example:
        >>> rules = VNMarketRules()
        >>> # Validate a complete trade
        >>> result = rules.validate_trade(
        ...     ticker="VNM",
        ...     action="sell",
        ...     quantity=150,
        ...     price=95000,
        ...     reference_price=100000,
        ...     purchase_date=datetime(2024, 1, 15),
        ...     trade_date=datetime(2024, 1, 18)
        ... )
    """

    def __init__(self):
        """Initialize VNMarketRules with default configurations."""
        self.exchanges = VN_EXCHANGES.copy()
        self.settlement_days = SETTLEMENT_DAYS
        self.default_lot_size = DEFAULT_LOT_SIZE
        self.ticker_exchange_map = TICKER_EXCHANGE_MAP.copy()

    def get_exchange(self, ticker: str) -> str:
        """
        Get the exchange for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Exchange code (HOSE, HNX, UPCOM)
        """
        return get_exchange_for_ticker(ticker)

    def get_exchange_info(self, exchange: str) -> dict:
        """
        Get configuration for an exchange.

        Args:
            exchange: Exchange code

        Returns:
            Dictionary with exchange configuration
        """
        return self.exchanges.get(exchange.upper(), self.exchanges["HOSE"])

    def validate_settlement(
        self,
        ticker: str,
        purchase_date: datetime,
        sell_date: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate T+2.5 settlement rule.

        Args:
            ticker: Stock ticker symbol
            purchase_date: Date when stock was purchased
            sell_date: Proposed sell date

        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_settlement(ticker, purchase_date, sell_date, raise_error=False)

    def round_lot_size(self, quantity: int, ticker: str = None) -> int:
        """
        Round quantity to valid lot size.

        Args:
            quantity: Requested number of shares
            ticker: Stock ticker (used to determine exchange)

        Returns:
            Rounded quantity
        """
        exchange = self.get_exchange(ticker) if ticker else "HOSE"
        return round_lot_size(quantity, exchange)

    def validate_lot_size(
        self,
        quantity: int,
        ticker: str = None
    ) -> Tuple[bool, Optional[str], int]:
        """
        Validate lot size.

        Args:
            quantity: Number of shares
            ticker: Stock ticker

        Returns:
            Tuple of (is_valid, error_message, corrected_quantity)
        """
        exchange = self.get_exchange(ticker) if ticker else "HOSE"
        return validate_lot_size(quantity, exchange, raise_error=False)

    def validate_price_limit(
        self,
        ticker: str,
        order_price: float,
        reference_price: float
    ) -> Tuple[bool, Optional[str], Tuple[float, float]]:
        """
        Validate price against daily limits.

        Args:
            ticker: Stock ticker symbol
            order_price: Proposed order price
            reference_price: Reference price (previous close)

        Returns:
            Tuple of (is_valid, error_message, (floor, ceiling))
        """
        return validate_price_limit(
            ticker, order_price, reference_price, raise_error=False
        )

    def get_price_limits(
        self,
        ticker: str,
        reference_price: float
    ) -> Tuple[float, float]:
        """
        Get price limits for a ticker.

        Args:
            ticker: Stock ticker symbol
            reference_price: Reference price

        Returns:
            Tuple of (floor_price, ceiling_price)
        """
        return get_price_limits(ticker, reference_price)

    def validate_trade(
        self,
        ticker: str,
        action: str,
        quantity: int,
        price: float = None,
        reference_price: float = None,
        purchase_date: datetime = None,
        trade_date: datetime = None,
        holdings: Dict[str, datetime] = None
    ) -> Dict:
        """
        Validate a complete trade against all Vietnam market rules.

        This is the main validation method that checks:
        1. Lot size (rounds down to valid quantity)
        2. Price limits (if price and reference_price provided)
        3. Settlement rules for sells (if purchase_date or holdings provided)

        Args:
            ticker: Stock ticker symbol
            action: Trade action ('buy' or 'sell')
            quantity: Number of shares
            price: Order price (optional)
            reference_price: Previous close price (required if price provided)
            purchase_date: Purchase date for sell validation (optional)
            trade_date: Date of the trade (defaults to today)
            holdings: Dictionary of ticker -> purchase_date (optional)

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "errors": list of error messages,
                "warnings": list of warning messages,
                "corrected_quantity": int,
                "price_limits": (floor, ceiling) or None,
                "exchange": exchange code
            }

        Example:
            >>> rules = VNMarketRules()
            >>> result = rules.validate_trade(
            ...     ticker="VNM",
            ...     action="buy",
            ...     quantity=150,
            ...     price=95000,
            ...     reference_price=100000
            ... )
            >>> print(result["is_valid"])
            True
            >>> print(result["corrected_quantity"])
            100
            >>> print(result["warnings"])
            ["Quantity rounded from 150 to 100 shares (lot size: 100)"]
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "corrected_quantity": quantity,
            "price_limits": None,
            "exchange": self.get_exchange(ticker),
        }

        trade_date = trade_date or datetime.now()
        action = action.lower().strip()

        # 1. Validate and correct lot size
        lot_valid, lot_msg, corrected_qty = self.validate_lot_size(quantity, ticker)
        if not lot_valid:
            if corrected_qty > 0:
                result["warnings"].append(
                    f"Quantity rounded from {quantity} to {corrected_qty} shares "
                    f"(lot size: {self.default_lot_size})"
                )
                result["corrected_quantity"] = corrected_qty
            else:
                result["is_valid"] = False
                result["errors"].append(lot_msg)
                result["corrected_quantity"] = 0

        # 2. Validate price limits (if price provided)
        if price is not None and reference_price is not None:
            price_valid, price_msg, limits = self.validate_price_limit(
                ticker, price, reference_price
            )
            result["price_limits"] = limits
            if not price_valid:
                result["is_valid"] = False
                result["errors"].append(price_msg)

        # 3. Validate settlement for sells
        if action == "sell":
            # Try to get purchase date from holdings dict or direct parameter
            sell_purchase_date = purchase_date
            if sell_purchase_date is None and holdings is not None:
                sell_purchase_date = holdings.get(ticker.upper())

            if sell_purchase_date is not None:
                settlement_valid, settlement_msg = self.validate_settlement(
                    ticker, sell_purchase_date, trade_date
                )
                if not settlement_valid:
                    result["is_valid"] = False
                    result["errors"].append(settlement_msg)

        return result

    def format_rules_summary(self, ticker: str = None) -> str:
        """
        Get a formatted summary of Vietnam market rules.

        This can be used to inject market rules into agent prompts.

        Args:
            ticker: Optional ticker to show specific exchange rules

        Returns:
            Formatted string describing the rules
        """
        exchange = self.get_exchange(ticker) if ticker else None
        exchange_info = self.get_exchange_info(exchange) if exchange else None

        summary = """
## Vietnam Stock Market Trading Rules

### Settlement Rule (T+2.5)
- Stocks purchased on day T can only be sold from the morning of T+3
- This means you must wait 2.5 business days after purchase to sell
- Attempting to sell before T+3 will result in a settlement error

### Lot Size Requirements
- All orders must be in multiples of 100 shares
- Orders with quantities not divisible by 100 will be rounded down
- Example: An order for 150 shares becomes 100 shares

### Daily Price Limits
"""
        if exchange_info:
            summary += f"""
For {exchange} ({exchange_info['name']}):
- Maximum daily movement: ±{exchange_info['price_limit_percent']}% from reference price
- Trading hours: {exchange_info['trading_hours']} ({exchange_info['timezone']})
"""
        else:
            summary += """
- HOSE (Ho Chi Minh Stock Exchange): ±7%
- HNX (Hanoi Stock Exchange): ±10%
- UPCOM (Unlisted Public Company Market): ±15%
"""
        summary += """
### Currency
- All prices are in Vietnamese Dong (VND)
- No fractional shares allowed
"""
        return summary.strip()
