# Data Ingestion Package

Production-ready data ingestion package for quantitative finance applications. Fetches market data from Yahoo Finance with built-in caching, rate limiting, and error handling.

## Features

- **Automatic Caching**: DuckDB-based persistent caching reduces API calls
- **Rate Limiting**: Token bucket algorithm respects API rate limits
- **Retry Logic**: Exponential backoff for handling transient failures
- **Data Validation**: Automatic validation of fetched data quality
- **Streamlit Integration**: Helper functions for seamless Streamlit integration
- **Comprehensive Error Handling**: Custom exceptions for different error scenarios

## Quick Start

```python
from src.data_ingestion import EquityFetcher

# Fetch stock data with automatic caching
fetcher = EquityFetcher()
df = fetcher.fetch_historical("AAPL", "2024-01-01", "2024-12-31")

print(df.head())
```

## Installation

All dependencies are already in `pyproject.toml`:
- yfinance >= 0.2.66
- duckdb >= 1.4.1
- pandas >= 2.2.3
- scipy >= 1.15.2

No additional packages needed!

---

## Data Fetchers & Data Items

### 1. Equity Data (`EquityFetcher`)

Fetch historical stock prices, OHLCV data, real-time quotes, and company information from Yahoo Finance.

#### 1.1 Historical OHLCV Data

Fetches Open, High, Low, Close, Volume (and Adj Close) time series for any Yahoo Finance symbol — individual stocks, ETFs, and market indices.

```python
from src.data_ingestion import EquityFetcher

fetcher = EquityFetcher()

# Daily prices for a single stock
df = fetcher.fetch_historical(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="1d"  # Options: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
)

# Returns DataFrame with columns: Open, High, Low, Close, Volume, Adj Close
print(df.head())
```

**Returned columns:**

| Column | Description |
|--------|-------------|
| `Open` | Opening price for the period |
| `High` | Highest price during the period |
| `Low` | Lowest price during the period |
| `Close` | Closing price for the period |
| `Volume` | Number of shares traded |
| `Adj Close` | Adjusted closing price (accounts for splits and dividends) |

**Quantitative finance use cases:**

| Use Case | Which Columns | Why |
|----------|---------------|-----|
| **Value at Risk (VaR)** | Close / Adj Close | Compute daily returns and estimate portfolio loss quantiles (historical, parametric, or Monte Carlo VaR) |
| **Backtesting** | Open, High, Low, Close, Volume | Simulate realistic trade execution with OHLCV bars; use Open for market-on-open orders, High/Low for stop/limit fills |
| **Volatility Modelling** | Close | Calculate realised volatility, fit GARCH / EWMA models for risk forecasting |
| **Portfolio Optimisation** | Adj Close | Build covariance matrices from adjusted returns for mean-variance optimisation |
| **Momentum / Factor Strategies** | Close, Volume | Compute price momentum signals, volume-weighted returns, and liquidity filters |
| **Technical Analysis** | Open, High, Low, Close, Volume | Candlestick patterns, moving averages, RSI, Bollinger Bands, VWAP |
| **Monte Carlo Simulation** | Close | Estimate drift and volatility parameters for Geometric Brownian Motion (GBM) simulations |
| **Correlation Analysis** | Close / Adj Close | Measure co-movement between assets for diversification and hedging |

**Supported symbol types:**

| Type | Example | Description |
|------|---------|-------------|
| US Stocks | `AAPL`, `MSFT`, `GOOGL` | Individual equities |
| ETFs | `SPY`, `QQQ`, `IWM` | Exchange-traded funds |
| Market Indices | `^GSPC`, `^DJI`, `^IXIC` | S&P 500, Dow Jones, NASDAQ |
| International | `HSBA.L`, `7203.T` | London, Tokyo exchanges |
| Crypto | `BTC-USD`, `ETH-USD` | Cryptocurrency pairs |

**Available intervals:**

| Interval | Code | Max History |
|----------|------|-------------|
| 1 minute | `1m` | 7 days |
| 2 minutes | `2m` | 60 days |
| 5 minutes | `5m` | 60 days |
| 15 minutes | `15m` | 60 days |
| 30 minutes | `30m` | 60 days |
| 60 minutes | `60m` | 730 days |
| 90 minutes | `90m` | 60 days |
| 1 hour | `1h` | 730 days |
| 1 day | `1d` | Full history |
| 5 days | `5d` | Full history |
| 1 week | `1wk` | Full history |
| 1 month | `1mo` | Full history |
| 3 months | `3mo` | Full history |

#### 1.2 Multiple Symbols (Batch Fetch)

Fetch the same date range for several symbols at once. Useful for portfolio and cross-asset analysis.

```python
# Fetch multiple symbols in one call
data = fetcher.fetch_multiple(
    symbols=["AAPL", "MSFT", "GOOGL", "AMZN"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Returns Dict[str, DataFrame]
for symbol, df in data.items():
    print(f"{symbol}: {len(df)} rows")
```

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Portfolio Optimisation (MPT)** | Build a multi-asset covariance matrix for Markowitz mean-variance optimisation |
| **Pairs Trading / Statistical Arbitrage** | Compute co-integration and spread series between related instruments |
| **Index Replication** | Track a basket of securities to replicate an index |
| **Cross-Asset VaR** | Estimate joint portfolio risk across multiple holdings |
| **Factor Analysis** | Regress individual stock returns against factor portfolios |

#### 1.3 Real-Time Quote

Fetch the latest intraday price snapshot for a single symbol.

```python
quote = fetcher.fetch_realtime_quote("AAPL")

print(f"Current price: ${quote['price']:.2f}")
print(f"Day range: ${quote['day_low']:.2f} - ${quote['day_high']:.2f}")
print(f"Volume: {quote['volume']:,}")
print(f"Market cap: ${quote['market_cap']:,.0f}")
```

**Returned fields:**

| Field | Description |
|-------|-------------|
| `symbol` | Ticker symbol |
| `price` | Current / last traded price |
| `previous_close` | Previous session close |
| `open` | Current session open |
| `day_high` | Intraday high |
| `day_low` | Intraday low |
| `volume` | Current session volume |
| `market_cap` | Market capitalisation |
| `currency` | Trading currency |

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Live Portfolio Valuation** | Mark-to-market current holdings in real time |
| **Intraday Risk Monitoring** | Track P&L and breach thresholds throughout the trading day |
| **Execution Benchmarking** | Compare fill prices against current quotes |

#### 1.4 Stock Information / Fundamentals

Fetch detailed company information, financials, and metadata.

```python
info = fetcher.get_info("AAPL")

print(f"Company: {info['longName']}")
print(f"Sector: {info['sector']}")
print(f"Industry: {info['industry']}")
print(f"Market Cap: ${info.get('marketCap', 0):,.0f}")
print(f"P/E Ratio: {info.get('trailingPE', 'N/A')}")
print(f"Dividend Yield: {info.get('dividendYield', 0):.2%}")
print(f"Beta: {info.get('beta', 'N/A')}")
```

**Key fields available:**

| Field | Description |
|-------|-------------|
| `longName` | Full company name |
| `sector` | Business sector |
| `industry` | Industry classification |
| `marketCap` | Market capitalisation |
| `trailingPE` | Trailing price-to-earnings ratio |
| `forwardPE` | Forward price-to-earnings ratio |
| `dividendYield` | Annual dividend yield |
| `beta` | Beta coefficient (market sensitivity) |
| `52WeekChange` | 52-week price change |
| `averageVolume` | Average daily volume |
| `shortRatio` | Short interest ratio |
| `bookValue` | Book value per share |
| `priceToBook` | Price-to-book ratio |
| `earningsGrowth` | Earnings growth rate |
| `revenueGrowth` | Revenue growth rate |
| `profitMargins` | Profit margins |

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Factor Models (Fama-French)** | Use book-to-market, size, and profitability for multi-factor construction |
| **Fundamental Screening** | Filter universes by P/E, dividend yield, market cap for value/growth strategies |
| **Risk Decomposition** | Use beta for systematic risk attribution |
| **Sector Rotation** | Allocate across sectors based on fundamental characteristics |
| **Dividend Discount Models** | Estimate intrinsic value from dividend yields and growth rates |

---

### 2. Options Data (`OptionsFetcher`)

Fetch options chains, available expirations, and implied volatility data from Yahoo Finance.

#### 2.1 Available Expirations

List all available options expiration dates for a given symbol.

```python
from src.data_ingestion import OptionsFetcher

fetcher = OptionsFetcher()

# Get all available expiration dates
expirations = fetcher.get_available_expirations("AAPL")
print(f"Available expirations: {expirations[:5]}")
# e.g. ['2026-02-28', '2026-03-07', '2026-03-14', ...]
```

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Term Structure Analysis** | Map implied volatility across expirations to build a volatility term structure |
| **Roll Strategy Planning** | Identify upcoming expirations for calendar spread or roll-over strategies |

#### 2.2 Options Chain (Calls & Puts)

Fetch the full options chain for a specific expiration, returning separate DataFrames for calls and puts.

```python
# Fetch options chain for a specific expiration
calls, puts = fetcher.fetch_option_chain(
    symbol="AAPL",
    expiration="2026-06-20"  # or None for nearest expiration
)

print(f"Found {len(calls)} call options and {len(puts)} put options")
print(calls[['Strike', 'Last', 'Bid', 'Ask', 'Volume', 'OpenInterest', 'ImpliedVolatility']].head())
```

**Returned columns (calls and puts):**

| Column | Description |
|--------|-------------|
| `contractSymbol` | Unique option contract identifier |
| `Strike` | Strike price |
| `Last` | Last traded price |
| `Bid` | Current bid price |
| `Ask` | Current ask price |
| `change` | Price change |
| `percentChange` | Percentage price change |
| `Volume` | Number of contracts traded |
| `OpenInterest` | Open interest (outstanding contracts) |
| `ImpliedVolatility` | Market-implied volatility |
| `inTheMoney` | Whether the option is in the money |
| `contractSize` | Contract size (typically REGULAR = 100 shares) |
| `lastTradeDate` | Timestamp of last trade |

**Quantitative finance use cases:**

| Use Case | Which Columns | Why |
|----------|---------------|-----|
| **Implied Volatility Surface** | Strike, ImpliedVolatility | Build the vol surface / smile across strikes and expirations |
| **Options Pricing (Black-Scholes)** | Strike, Last, Bid, Ask, ImpliedVolatility | Calibrate and validate theoretical pricing models |
| **Greeks Calculation** | Strike, ImpliedVolatility, Last | Compute delta, gamma, theta, vega for hedging and risk management |
| **Put-Call Parity Checks** | Strike, Bid, Ask (calls & puts) | Verify no-arbitrage relationships between calls and puts |
| **Volatility Trading** | ImpliedVolatility, Volume, OpenInterest | Identify mispriced options and construct volatility spread strategies |
| **Hedging (Delta Hedging)** | Strike, ImpliedVolatility | Select optimal strikes for portfolio hedging |
| **Liquidity Analysis** | Volume, OpenInterest, Bid, Ask | Assess option liquidity and bid-ask spread for execution cost estimation |
| **Skew & Kurtosis Analysis** | Strike, ImpliedVolatility | Measure volatility skew (put-call IV differences) for tail risk assessment |
| **Risk-Neutral Density** | Strike, Bid, Ask | Extract market-implied probability distributions of future prices |

#### 2.3 Options with Greeks

Fetch an options chain filtered by option type. Note: yfinance provides implied volatility natively; for full Greeks (delta, gamma, theta, vega), use scipy or a dedicated pricing library.

```python
# Get call options with available Greeks
greeks_df = fetcher.fetch_greeks("AAPL", "2026-06-20", option_type="call")
print(greeks_df[['Strike', 'Last', 'ImpliedVolatility']].head())

# For full Greeks, combine with Black-Scholes calculation
# (see app_quant_finance for implementations)
```

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Portfolio Greeks** | Aggregate option sensitivities across a book of positions |
| **Dynamic Hedging** | Continuously rebalance delta-neutral positions |
| **Risk Limits Monitoring** | Track gamma, vega exposure against predefined limits |

---

### 3. Fixed Income Data (`FixedIncomeFetcher`)

Fetch US Treasury yields and yield curves from Yahoo Finance treasury indices.

#### 3.1 Treasury Yields (Time Series)

Fetch historical yield data for one or more maturities over a date range.

```python
from src.data_ingestion import FixedIncomeFetcher

fetcher = FixedIncomeFetcher()

# Fetch 10-year and 30-year treasury yields
yields = fetcher.fetch_treasury_yields(
    maturities=["10Y", "30Y"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)

print(yields.head())
# Returns DataFrame with maturities as columns and dates as index
```

**Available maturities and Yahoo Finance symbols:**

| Maturity | Yahoo Symbol | Description |
|----------|-------------|-------------|
| `3M` | `^IRX` | 13-week Treasury bill |
| `6M` | `^IRX` | 6-month Treasury (approximated via 13-week) |
| `1Y` | `^IRX` | 1-year Treasury (approximated via 13-week) |
| `2Y` | `^FVX` | 2-year Treasury (approximated via 5-year index) |
| `5Y` | `^FVX` | 5-year Treasury yield |
| `10Y` | `^TNX` | 10-year Treasury yield |
| `30Y` | `^TYX` | 30-year Treasury yield |

> **Note:** Some shorter maturities (6M, 1Y, 2Y) are approximations because Yahoo Finance does not provide dedicated indices for every tenor. The 3M, 5Y, 10Y, and 30Y are the most accurate.

**Quantitative finance use cases:**

| Use Case | Which Maturities | Why |
|----------|-----------------|-----|
| **Risk-Free Rate** | 3M, 10Y | Required input for Black-Scholes, CAPM, and most pricing models |
| **Bond Pricing / Valuation** | All | Discount future cash flows to present value |
| **Duration & Convexity** | Multiple | Measure interest rate sensitivity of fixed income portfolios |
| **Interest Rate VaR** | 10Y, 30Y | Estimate potential losses from yield movements |
| **Yield Spread Analysis** | 2Y, 10Y | Monitor the 2s10s spread as a recession indicator |
| **Discount Curve Construction** | All | Bootstrap a zero-coupon curve for derivatives pricing |
| **Fixed Income Backtesting** | All | Test bond trading strategies against historical yield data |
| **Macro Factor Models** | 10Y, 30Y | Use yield levels and changes as factors in multi-asset models |

#### 3.2 Yield Curve (Cross-Sectional Snapshot)

Fetch the yield curve for a specific date — yields across all available maturities at a single point in time.

```python
# Get yield curve for a specific date
curve = fetcher.fetch_yield_curve("2024-12-31")
print(curve)
# Returns DataFrame with columns: Maturity, Yield
```

**Quantitative finance use cases:**

| Use Case | Why |
|----------|-----|
| **Curve Shape Analysis** | Determine if the curve is normal, inverted, or flat — key recession signal |
| **Interpolation (Bootstrapping)** | Fit Nelson-Siegel, Svensson, or cubic spline models to the observed curve |
| **Relative Value Trading** | Identify rich/cheap points along the curve for butterfly and barbell trades |
| **Scenario Analysis** | Stress-test portfolios under parallel shifts, steepening, or flattening scenarios |
| **Swap Pricing** | Use the curve as the floating leg reference for interest rate swaps |

#### 3.3 Available Maturities

List all supported maturities.

```python
maturities = fetcher.get_available_maturities()
print(f"Available: {maturities}")
# ['3M', '6M', '1Y', '2Y', '5Y', '10Y', '30Y']
```

---

## Caching

### Automatic Caching

All fetchers automatically cache data in DuckDB. Repeated requests for the same data are served from the local cache, drastically reducing API calls and improving performance.

```python
# First call — fetches from Yahoo Finance API
df1 = fetcher.fetch_historical("AAPL", "2024-01-01", "2024-12-31")

# Second call — returned from local DuckDB cache (much faster)
df2 = fetcher.fetch_historical("AAPL", "2024-01-01", "2024-12-31")
```

### Cache TTLs by Data Type

| Data Type | Default TTL | Rationale |
|-----------|-------------|-----------|
| Equity (historical) | 1 hour | Historical data changes infrequently |
| Options chains | 30 minutes | Options prices update throughout the trading day |
| Fixed income | 1 hour | Treasury yields update daily |

### Cache Management

```python
from src.data_ingestion import CacheManager

manager = CacheManager()

# Get cache statistics
summary = manager.get_summary()
print(f"Cache size: {summary['size_mb']:.2f} MB")
print(f"Total entries: {summary['total_entries']}")

# Print formatted summary
manager.print_summary()

# Clean up expired entries
removed = manager.cleanup_expired_entries()
print(f"Removed {removed} expired entries")

# Invalidate specific table
manager.invalidate_table("equity_cache", confirm=True)

# Invalidate entire cache
manager.invalidate_all(confirm=True)

# Auto-cleanup if too many expired entries
manager.auto_cleanup_if_needed(max_expired_ratio=0.2, min_expired_count=10)
```

### Cache Tables

| Table | Stored By | Key Format |
|-------|-----------|------------|
| `equity_cache` | `EquityFetcher` | `equity:{symbol}:{start}:{end}:{interval}` |
| `options_cache` | `OptionsFetcher` | `options:{symbol}:{expiration}` |
| `fixed_income_cache` | `FixedIncomeFetcher` | `fixedincome:{maturities}:{start}:{end}` |

### Cache Location

- Default: `~/.quant_finance/cache.duckdb`
- Configurable via `QUANT_FINANCE_CACHE_DIR` environment variable or `DataIngestionConfig`

---

## Configuration

### Using Environment Variables

```bash
export QUANT_FINANCE_CACHE_DIR=~/.quant_finance
export QUANT_FINANCE_CACHE_TTL=7200
export QUANT_FINANCE_RATE_LIMIT=2.0
export QUANT_FINANCE_RATE_LIMIT_BURST=10
export QUANT_FINANCE_MAX_RETRIES=3
export QUANT_FINANCE_RETRY_BASE_DELAY=1.0
export QUANT_FINANCE_RETRY_MAX_DELAY=60.0
export QUANT_FINANCE_VALIDATE_DATA=true
```

### Programmatic Configuration

```python
from src.data_ingestion import DataIngestionConfig, EquityFetcher

# Custom configuration
config = DataIngestionConfig(
    cache_dir="/custom/path",
    default_ttl_seconds=7200,       # 2 hours
    rate_limit_per_second=1.5,
    rate_limit_burst=10,
    max_retries=5,
    retry_base_delay=1.0,
    retry_max_delay=60.0,
    validate_data=True,
    allow_partial_data=False,
    auto_adjust=True,               # yfinance auto-adjust prices
    threads=True,                   # yfinance threading
)

# Use with any fetcher
fetcher = EquityFetcher(config=config)
```

### Default Configuration Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cache_dir` | `~/.quant_finance` | Cache database directory |
| `cache_db_name` | `cache.duckdb` | Cache database filename |
| `default_ttl_seconds` | `3600` (1 hour) | Cache time-to-live |
| `rate_limit_per_second` | `2.0` | API requests per second |
| `rate_limit_burst` | `10` | Maximum burst capacity |
| `max_retries` | `3` | Retry attempts on failure |
| `retry_base_delay` | `1.0` | Initial retry delay (seconds) |
| `retry_max_delay` | `60.0` | Maximum retry delay (seconds) |
| `validate_data` | `True` | Enable data quality validation |
| `allow_partial_data` | `False` | Allow incomplete data |
| `auto_adjust` | `True` | yfinance auto-adjust for splits/dividends |
| `threads` | `True` | yfinance multi-threading |

---

## Streamlit Integration

### Helper Functions

```python
import streamlit as st
from src.data_ingestion.streamlit_helpers import (
    get_stock_data,
    get_options_chain,
    get_treasury_yields,
    display_fetch_status
)

# Cached stock data fetcher (TTL: 1 hour)
df = get_stock_data("AAPL", "2024-01-01", "2024-12-31")
st.dataframe(df)

# Cached options fetcher (TTL: 30 minutes)
calls, puts = get_options_chain("AAPL", "2026-06-20")
st.dataframe(calls)

# Cached treasury yields (TTL: 6 hours)
yields = get_treasury_yields(["10Y", "30Y"], "2024-01-01", "2024-12-31")
st.line_chart(yields)

# Display with automatic error handling and spinner
df = display_fetch_status(
    get_stock_data,
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
if df is not None:
    st.line_chart(df['Close'])
```

### Ready-Made Widgets

```python
import streamlit as st
from src.data_ingestion.streamlit_helpers import (
    create_stock_data_widget,
    create_options_widget,
    format_market_data_summary
)

st.title("Stock Data Dashboard")

# Complete stock data widget with input controls
df = create_stock_data_widget()
if df is not None:
    # Format and display metrics
    summary = format_market_data_summary(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Close", f"${summary['latest_close']:.2f}")
    col2.metric("Change", f"${summary['change']:.2f}", f"{summary['change_pct']:.2f}%")
    col3.metric("Period Return", f"{summary['period_return']:.2f}%")

    st.line_chart(df['Close'])

# Options widget with dynamic expiration loading
result = create_options_widget()
if result:
    calls, puts = result
    st.subheader("Call Options")
    st.dataframe(calls)
```

### Custom Caching Decorator

```python
from src.data_ingestion.streamlit_helpers import st_cache_data_ingestion

@st_cache_data_ingestion(ttl=3600, show_spinner=True)
def load_custom_data(symbol):
    fetcher = EquityFetcher()
    return fetcher.fetch_historical(symbol, "2024-01-01", "2024-12-31")
```

---

## Error Handling

The package provides a custom exception hierarchy for granular error handling:

```
DataIngestionError (base)
├── FetchError               — General fetch failure (network, API)
│   ├── SymbolNotFoundError  — Ticker symbol not recognised
│   └── RateLimitError       — API rate limit exceeded
├── CacheError               — Cache read/write failure
├── ValidationError          — Data quality check failure
└── ConfigurationError       — Invalid configuration
```

```python
from src.data_ingestion import (
    EquityFetcher,
    SymbolNotFoundError,
    ValidationError,
    RateLimitError,
    FetchError,
    CacheError,
)

fetcher = EquityFetcher()

try:
    df = fetcher.fetch_historical("INVALID_SYMBOL", "2024-01-01", "2024-12-31")
except SymbolNotFoundError as e:
    print(f"Symbol not found: {e}")
except ValidationError as e:
    print(f"Invalid input or data quality failure: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded — retry after a delay: {e}")
except FetchError as e:
    print(f"Failed to fetch data (network/API error): {e}")
except CacheError as e:
    print(f"Cache error: {e}")
```

---

## Rate Limiting

Automatic rate limiting using the token bucket algorithm prevents excessive API calls:

```python
# Default: 2 requests/second with burst of 10
# Automatically applied to all fetcher calls

fetcher = EquityFetcher()

# These calls are automatically rate-limited
for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]:
    df = fetcher.fetch_historical(symbol, "2024-01-01", "2024-12-31")
    print(f"Fetched {symbol}: {len(df)} rows")
```

### Manual Rate Limiter Usage

```python
from src.data_ingestion.utils.rate_limiter import TokenBucketLimiter

limiter = TokenBucketLimiter(tokens_per_second=2.0, bucket_size=10)

# Context manager usage
with limiter.throttle():
    # Your API call here
    pass

# Check available tokens
print(f"Available tokens: {limiter.get_available_tokens()}")
```

---

## Data Validation

Automatic data quality validation is applied to all fetched data:

### Equity Validation
- Required columns exist (Open, High, Low, Close, Volume)
- Prices are positive
- High >= Low for every row
- No completely null rows
- Strict mode: no null values at all

### Options Validation
- Required columns exist (Strike, Last, Volume, OpenInterest)
- Strikes are positive
- Prices are non-negative

### Fixed Income Validation
- Data is non-empty
- Yields are non-negative
- Yields are reasonable (< 100%)

### Manual Validation

```python
from src.data_ingestion.utils.validators import DataValidator

# Validate a DataFrame directly
is_valid = DataValidator.validate_equity_data(df, strict=True)

# Validate date ranges
DataValidator.validate_date_range("2024-01-01", "2024-12-31")  # True
DataValidator.validate_date_range("2024-12-31", "2024-01-01")  # False

# Validate symbols
DataValidator.validate_symbol("AAPL")   # True
DataValidator.validate_symbol("")       # False

# Validate intervals
DataValidator.validate_interval("1d")   # True
DataValidator.validate_interval("2d")   # False
```

---

## Advanced Usage

### Custom Retry Strategy

```python
from src.data_ingestion.utils.retry import ExponentialBackoffRetry

retry_strategy = ExponentialBackoffRetry(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    exponential_base=2.0
)

# Use as decorator
@retry_strategy
def fetch_data():
    # Your fetch logic here
    pass

# Or execute directly
result = retry_strategy.execute(fetcher.fetch_historical, "AAPL", "2024-01-01", "2024-12-31")
```

**Retryable errors** (automatically retried):
- `RateLimitError`, `FetchError` (network errors)
- Timeout, connection, and temporary errors
- Server errors (HTTP 500, 502, 503, 504)

**Non-retryable errors** (fail immediately):
- `ValidationError`, `SymbolNotFoundError`

### Cache Bypass

```python
# Force a fresh fetch, ignoring any cached data
df = fetcher.fetch_historical(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31",
    use_cache=False
)
```

### Cache Invalidation

```python
# Invalidate a specific cache entry
fetcher.invalidate_cache(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

---

## Data Items Summary

A complete reference of every data item available through the package, with corresponding quantitative finance applications:

| # | Data Item | Fetcher | Method | Key Use Cases |
|---|-----------|---------|--------|---------------|
| 1 | Historical OHLCV (single) | `EquityFetcher` | `fetch_historical()` | VaR, backtesting, volatility modelling, Monte Carlo |
| 2 | Historical OHLCV (batch) | `EquityFetcher` | `fetch_multiple()` | Portfolio optimisation, correlation, factor models |
| 3 | Real-time quote | `EquityFetcher` | `fetch_realtime_quote()` | Live P&L, intraday risk monitoring |
| 4 | Stock info / fundamentals | `EquityFetcher` | `get_info()` | Factor models, fundamental screening, CAPM beta |
| 5 | Options expirations | `OptionsFetcher` | `get_available_expirations()` | Term structure analysis, roll planning |
| 6 | Options chain (calls & puts) | `OptionsFetcher` | `fetch_option_chain()` | Vol surface, options pricing, Greeks, hedging |
| 7 | Options by type (with Greeks) | `OptionsFetcher` | `fetch_greeks()` | Portfolio Greeks, dynamic hedging |
| 8 | Treasury yields (time series) | `FixedIncomeFetcher` | `fetch_treasury_yields()` | Risk-free rate, bond pricing, interest rate VaR |
| 9 | Yield curve (snapshot) | `FixedIncomeFetcher` | `fetch_yield_curve()` | Curve fitting, relative value, scenario analysis |
| 10 | Available maturities | `FixedIncomeFetcher` | `get_available_maturities()` | Discovery / configuration |

---

## Package Structure

```
src/data_ingestion/
├── __init__.py                 # Package exports
├── config.py                   # Configuration management (DataIngestionConfig)
├── exceptions.py               # Custom exception hierarchy
├── streamlit_helpers.py        # Streamlit integration (widgets, caching, display)
├── base/
│   ├── fetcher.py              # Abstract base fetcher (cache-or-fetch pattern)
│   └── cache.py                # Abstract cache interface
├── cache/
│   ├── duckdb_cache.py         # DuckDB persistent caching implementation
│   └── cache_manager.py        # High-level cache management (stats, cleanup)
├── fetchers/
│   ├── equity.py               # EquityFetcher — stocks, ETFs, indices
│   ├── options.py              # OptionsFetcher — options chains and Greeks
│   └── fixed_income.py         # FixedIncomeFetcher — treasury yields and curves
└── utils/
    ├── rate_limiter.py         # Token bucket rate limiter
    ├── retry.py                # Exponential backoff retry strategy
    └── validators.py           # Data quality validation
```

---

## Performance Tips

1. **Use caching** — first call fetches from the API, subsequent calls use the local DuckDB cache
2. **Batch requests** — use `fetch_multiple()` for multiple symbols rather than looping with `fetch_historical()`
3. **Set appropriate TTLs** — longer TTL for historical data, shorter for live/options data
4. **Clean up regularly** — run `manager.cleanup_expired_entries()` or `manager.auto_cleanup_if_needed()` periodically
5. **Monitor cache size** — check statistics with `manager.get_summary()`
6. **Use intervals wisely** — intraday data (`1m`, `5m`) has limited history; daily data goes back decades

---

## Troubleshooting

### Cache Issues

```python
# Check cache location
from src.data_ingestion import get_default_config
config = get_default_config()
print(f"Cache location: {config.cache_db_path}")

# Clear cache if corrupted
from src.data_ingestion import CacheManager
manager = CacheManager()
manager.invalidate_all(confirm=True)
```

### Rate Limit Errors

```python
# Reduce request rate
from src.data_ingestion import DataIngestionConfig, EquityFetcher
config = DataIngestionConfig(rate_limit_per_second=1.0)
fetcher = EquityFetcher(config=config)
```

### Validation Errors

```python
# Allow partial / incomplete data
from src.data_ingestion import DataIngestionConfig, EquityFetcher
config = DataIngestionConfig(allow_partial_data=True)
fetcher = EquityFetcher(config=config)
```

### No Data Returned

```python
# Verify the symbol is valid
from src.data_ingestion.utils.validators import DataValidator
print(DataValidator.validate_symbol("AAPL"))  # True

# Check if it's a weekend/holiday date range
# Yahoo Finance only has data for trading days
```

---

## Exports Reference

All public exports from `src.data_ingestion`:

```python
# Configuration
from src.data_ingestion import DataIngestionConfig, get_default_config, set_default_config

# Fetchers
from src.data_ingestion import EquityFetcher, OptionsFetcher, FixedIncomeFetcher

# Cache
from src.data_ingestion import DuckDBCache, CacheManager, create_cache_manager

# Exceptions
from src.data_ingestion import (
    DataIngestionError, FetchError, CacheError,
    RateLimitError, ValidationError, SymbolNotFoundError, ConfigurationError
)

# Utilities
from src.data_ingestion import DataValidator, TokenBucketLimiter, ExponentialBackoffRetry, retry_on_exception
```

---

## License

MIT License — Part of the Quantitative Finance Project
