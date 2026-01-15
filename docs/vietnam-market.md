# Vietnam Stock Market Support

TradingAgents supports the Vietnamese stock market (HOSE, HNX, UPCOM exchanges) through the `vnstock` data provider and Vietnam-specific trading rules integration.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Supported Exchanges](#supported-exchanges)
- [Vietnam Market Trading Rules](#vietnam-market-trading-rules)
- [Data Sources](#data-sources)
- [Example Usage](#example-usage)
- [Agent Behavior](#agent-behavior)
- [Docker Deployment](#docker-deployment)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies

```bash
# Install vnstock3 for Vietnamese stock data
pip install vnstock3

# Or install all dependencies
pip install -r requirements.txt
```

### 2. Configure for Vietnam Market

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_market_config

# Get Vietnam market configuration
config = get_market_config("vn")

# Initialize TradingAgents with Vietnam market
ta = TradingAgentsGraph(debug=True, config=config)

# Analyze a Vietnamese stock
_, decision = ta.propagate("FPT", "2024-11-15")
print(decision)
```

---

## Configuration

### Market Configuration Options

In `tradingagents/default_config.py`, set the market type:

```python
# For US market (default)
config["market"] = "us"

# For Vietnam market
config["market"] = "vn"
```

### Using the Helper Function

The `get_market_config()` helper function provides a convenient way to get market-specific configuration:

```python
from tradingagents.default_config import get_market_config

# Get default US config
us_config = get_market_config("us")

# Get Vietnam-specific config
vn_config = get_market_config("vn")
```

### Vietnam Market Config Preset

The `VN_MARKET_CONFIG` preset automatically configures all data vendors for Vietnam:

```python
VN_MARKET_CONFIG = {
    "market": "vn",
    "data_vendors": {
        "core_stock_apis": "vnstock",        # Vietnam stock data via vnstock library
        "technical_indicators": "vnstock",   # Technical indicators calculated from vnstock data
        "fundamental_data": "vnstock",       # Vietnamese company financials via vnstock
        "news_data": "vnstock",              # Vietnamese news from CafeF, Vietstock, VnExpress
    },
}
```

### Environment Variables

You can also configure via environment variables:

```bash
export TRADINGAGENTS_MARKET=vn
export TRADINGAGENTS_RESULTS_DIR=./results
```

---

## Supported Exchanges

TradingAgents supports all three major Vietnamese stock exchanges:

| Exchange | Name | Price Limit | Trading Hours (ICT) |
|----------|------|-------------|---------------------|
| **HOSE** | Ho Chi Minh Stock Exchange | ±7% | 09:00-11:30, 13:00-15:00 |
| **HNX** | Hanoi Stock Exchange | ±10% | 09:00-11:30, 13:00-15:00 |
| **UPCOM** | Unlisted Public Company Market | ±15% | 09:00-11:30, 13:00-15:00 |

### Trading Sessions

- **ATO (At-The-Open)**: 09:00 - 09:15
- **Continuous Trading**: 09:15 - 11:30, 13:00 - 14:30
- **ATC (At-The-Close)**: 14:30 - 14:45
- **Put-through**: 14:45 - 15:00

---

## Vietnam Market Trading Rules

### T+2.5 Settlement Rule

Vietnamese stocks follow a T+2.5 settlement rule, meaning:
- Stocks purchased on day T cannot be sold until the **morning of day T+3**
- This is enforced automatically by the Risk Manager agent

```python
from tradingagents.rules.vn_market_rules import VNMarketRules

rules = VNMarketRules()

# Check if a stock can be sold
can_sell = rules.can_sell_today(
    purchase_date="2024-11-11",  # Monday
    check_date="2024-11-14"      # Thursday - can sell
)
print(f"Can sell: {can_sell}")  # True
```

### Lot Size Requirements

All orders must be in multiples of **100 shares**:

```python
from tradingagents.rules.vn_market_rules import VNMarketRules

rules = VNMarketRules()

# Round order quantity to valid lot size
original_qty = 150
rounded_qty = rules.round_lot_size(original_qty)
print(f"Rounded: {rounded_qty}")  # 100
```

### Price Limit Validation

Price limits vary by exchange and are enforced automatically:

```python
from tradingagents.rules.vn_market_rules import VNMarketRules

rules = VNMarketRules()

# Validate price against limits
reference_price = 50000  # VND
try:
    rules.validate_price_limit("FPT", 55000, reference_price)  # Within ±7% for HOSE
    print("Price is valid")
except PriceLimitError as e:
    print(f"Invalid price: {e}")

# Get price limits
floor_price, ceiling_price = rules.get_price_limits("FPT", reference_price)
print(f"Valid range: {floor_price:,.0f} - {ceiling_price:,.0f} VND")
```

---

## Data Sources

### Stock Data (vnstock)

The `vnstock` library provides access to Vietnamese stock market data:

- **OHLCV data**: Open, High, Low, Close, Volume
- **Financial statements**: Balance sheet, Income statement, Cash flow
- **Financial ratios**: P/E, P/B, ROE, ROA, etc.
- **Company information**: Overview, profile, ownership structure

### News Sources

Vietnamese news is fetched from multiple sources:

| Source | Type | Coverage |
|--------|------|----------|
| **CafeF** | Financial news portal | Market news, company updates |
| **Vietstock** | Stock market news | Analysis, earnings reports |
| **VnExpress** | General news | Economy, business section |

### Technical Indicators

All standard indicators are calculated from vnstock data:

- Moving averages: SMA, EMA, VWMA
- Momentum: RSI, MACD, MFI
- Volatility: Bollinger Bands, ATR
- Volume: Volume-weighted metrics

---

## Example Usage

### Basic Vietnam Stock Analysis

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import get_market_config

# Configure for Vietnam
config = get_market_config("vn")
config["deep_think_llm"] = "gpt-4o"
config["quick_think_llm"] = "gpt-4o-mini"

# Initialize
ta = TradingAgentsGraph(debug=True, config=config)

# Analyze popular Vietnamese stocks
tickers = ["VNM", "FPT", "TCB", "HPG", "MWG"]
for ticker in tickers:
    _, decision = ta.propagate(ticker, "2024-11-15")
    print(f"{ticker}: {decision['action']}")
```

### With Holdings Tracking

```python
from tradingagents.agents.utils.agent_states import (
    create_vn_holding,
    can_sell_holding,
    get_holdings_summary
)
from datetime import date

# Create holdings records
holdings = [
    create_vn_holding("FPT", 500, "2024-11-11", purchase_price=120000),
    create_vn_holding("VNM", 300, "2024-11-13", purchase_price=80000),
]

# Check which can be sold today
today = date(2024, 11, 14)  # Thursday
for holding in holdings:
    sellable = can_sell_holding(holding, today.isoformat())
    status = "CAN SELL" if sellable else "LOCKED"
    print(f"{holding['ticker']}: {status}")

# Get formatted summary
summary = get_holdings_summary(holdings, today.isoformat())
print(summary)
```

### CLI Usage

```bash
# Start the CLI
python -m cli.main

# Select Vietnam market from the menu
# Enter Vietnamese ticker (e.g., FPT, VNM, TCB)
```

---

## Agent Behavior

When `market="vn"` is configured, all agents adapt their behavior:

### Fundamentals Analyst
- Uses Vietnamese accounting standards (VAS) context
- References Vietnamese financial documents:
  - Consolidated Financial Statements (Bao cao tai chinh hop nhat)
  - Balance Sheet (Bang can doi ke toan)
  - Income Statement (Bao cao ket qua kinh doanh)
- Focuses on Vietnam-specific sectors: Banking, Real Estate, Securities

### Market Analyst
- References VN-Index, HNX-Index, VN30-Index
- Understands Vietnam trading hours and sessions
- Monitors foreign ownership (Khoi ngoai) as sentiment indicator

### News Analyst
- Prioritizes Vietnamese news sources (CafeF, Vietstock, VnExpress)
- Understands SBV (State Bank of Vietnam) policy impact
- Tracks sector-specific news for Banking and Real Estate

### Trader Agent
- Aware of T+2.5 settlement rules
- Respects lot size requirements (multiples of 100)
- Considers exchange-specific price limits in orders

### Risk Manager
- Enforces T+2.5 settlement rule (blocks early selling)
- Validates lot sizes before approving trades
- Checks price limits based on exchange

---

## Docker Deployment

### Using Docker Compose

```bash
# Start all services (app + Redis cache)
docker-compose up -d

# View logs
docker-compose logs -f tradingagents

# Stop services
docker-compose down
```

### Environment Configuration

Create a `.env` file with your configuration:

```env
# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...  # Optional

# Market Configuration
TRADINGAGENTS_MARKET=vn

# Optional: Redis for caching
REDIS_HOST=redis
REDIS_PORT=6379
```

### Docker Compose for Vietnam Market

```yaml
version: '3.8'

services:
  tradingagents:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TRADINGAGENTS_MARKET=vn
    volumes:
      - ./results:/app/results
      - ./data/cache:/app/data/cache
```

---

## Known Limitations

### Data Availability

1. **Historical data depth**: vnstock provides limited historical data compared to US market providers
2. **Real-time data**: Data may have slight delays (15-30 minutes) depending on the source
3. **Corporate actions**: Stock splits, dividends may not be automatically adjusted

### Market Rules

1. **Exchange detection**: Some lesser-known tickers may default to HOSE if exchange cannot be determined
2. **Holiday calendar**: Vietnamese holidays are not automatically detected; manual verification may be needed
3. **Foreign ownership limits**: Not currently enforced in validation

### Technical

1. **Rate limiting**: vnstock and news sources may rate-limit requests; caching is recommended
2. **Network dependency**: Requires internet connection for data fetching (no offline mode)
3. **Vietnamese text**: Some news content may be in Vietnamese; LLM handles translation

### News Sources

1. **Coverage**: Not all stocks have comprehensive news coverage
2. **Timeliness**: News aggregation may have delays
3. **Language**: Mix of Vietnamese and English content

---

## Troubleshooting

### Common Issues

#### "vnstock module not found"

```bash
pip install vnstock3
# or
pip install vnstock  # for older version
```

#### "No data available for ticker"

- Verify ticker symbol is correct (e.g., `FPT` not `FPT.VN`)
- Check if market is open (weekdays, Vietnam time)
- Some tickers may have limited data availability

#### "Settlement rule violation"

The T+2.5 rule is being enforced. Stocks cannot be sold until the morning of T+3.

#### Slow data fetching

Enable caching to improve performance:

```python
from tradingagents.dataflows.cache import get_cache

cache = get_cache()
cache.cleanup_expired()  # Clear old cache entries
```

### Getting Help

- Check the [TradingAgents Discord](https://discord.com/invite/hk9PGKShPK) for community support
- Open an issue on GitHub for bugs or feature requests
- Review the vnstock documentation at [vnstock.site](https://vnstock.site/)

---

## Appendix: Supported Tickers

### Major HOSE Tickers

| Ticker | Company | Sector |
|--------|---------|--------|
| VNM | Vinamilk | Consumer Goods |
| VIC | Vingroup | Real Estate |
| VHM | Vinhomes | Real Estate |
| HPG | Hoa Phat Group | Steel |
| FPT | FPT Corporation | Technology |
| MWG | Mobile World Group | Retail |
| VCB | Vietcombank | Banking |
| BID | BIDV | Banking |
| CTG | VietinBank | Banking |
| TCB | Techcombank | Banking |
| VPB | VP Bank | Banking |
| MBB | Military Bank | Banking |
| ACB | Asia Commercial Bank | Banking |
| SSI | SSI Securities | Securities |
| VND | VNDirect Securities | Securities |

### Major HNX Tickers

| Ticker | Company | Sector |
|--------|---------|--------|
| PVS | PV Drilling | Oil & Gas |
| SHB | SHB Bank | Banking |
| NVB | NCB Bank | Banking |
| CEO | CEO Group | Real Estate |
| HUT | TASCO | Infrastructure |

---

## Version History

- **v1.0.0** (2026-01): Initial Vietnam market support
  - vnstock integration for HOSE, HNX, UPCOM
  - T+2.5 settlement rule enforcement
  - Vietnamese news sources (CafeF, Vietstock, VnExpress)
  - Vietnam-specific agent prompts
  - Docker support with caching
