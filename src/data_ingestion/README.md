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
df = fetcher.fetch_historical("AAPL", "2023-01-01", "2023-12-31")

print(df.head())
```

## Installation

All dependencies are already in `pyproject.toml`:
- yfinance >= 0.2.66
- duckdb >= 1.4.1
- pandas >= 2.2.3
- scipy >= 1.15.2

No additional packages needed!

## Data Fetchers

### Equity Data

Fetch historical stock prices, OHLCV data, and stock information.

```python
from src.data_ingestion import EquityFetcher

fetcher = EquityFetcher()

# Fetch historical data
df = fetcher.fetch_historical(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31",
    interval="1d"  # Options: 1m, 5m, 1h, 1d, 1wk, 1mo
)

# Fetch multiple symbols
data = fetcher.fetch_multiple(
    symbols=["AAPL", "MSFT", "GOOGL"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# Get real-time quote
quote = fetcher.fetch_realtime_quote("AAPL")
print(f"Current price: ${quote['price']:.2f}")

# Get stock information
info = fetcher.get_info("AAPL")
print(f"Company: {info['longName']}")
print(f"Sector: {info['sector']}")
```

### Options Data

Fetch options chains, expirations, and Greeks.

```python
from src.data_ingestion import OptionsFetcher

fetcher = OptionsFetcher()

# Get available expirations
expirations = fetcher.get_available_expirations("AAPL")
print(f"Available expirations: {expirations}")

# Fetch options chain
calls, puts = fetcher.fetch_option_chain(
    symbol="AAPL",
    expiration="2024-01-19"
)

print(f"Found {len(calls)} call options")
print(calls[['Strike', 'Last', 'ImpliedVolatility']].head())

# Get options with Greeks
greeks_df = fetcher.fetch_greeks("AAPL", "2024-01-19", option_type="call")
```

### Fixed Income Data

Fetch treasury yields and yield curves.

```python
from src.data_ingestion import FixedIncomeFetcher

fetcher = FixedIncomeFetcher()

# Fetch treasury yields
yields = fetcher.fetch_treasury_yields(
    maturities=["10Y", "30Y"],
    start_date="2023-01-01",
    end_date="2023-12-31"
)

print(yields.head())

# Get yield curve for specific date
curve = fetcher.fetch_yield_curve("2023-12-31")
print(curve)

# See available maturities
maturities = fetcher.get_available_maturities()
print(f"Available: {maturities}")
```

## Caching

### Automatic Caching

All fetchers automatically cache data in DuckDB:

```python
# First call - fetches from API
df1 = fetcher.fetch_historical("AAPL", "2023-01-01", "2023-12-31")

# Second call - returns from cache (much faster!)
df2 = fetcher.fetch_historical("AAPL", "2023-01-01", "2023-12-31")
```

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
```

### Cache Location

- Default: `~/.quant_finance/cache.duckdb`
- Configurable via environment variable or config

## Configuration

### Using Environment Variables

```bash
export QUANT_FINANCE_CACHE_DIR=~/.quant_finance
export QUANT_FINANCE_CACHE_TTL=7200
export QUANT_FINANCE_RATE_LIMIT=2.0
export QUANT_FINANCE_MAX_RETRIES=3
```

### Programmatic Configuration

```python
from src.data_ingestion import DataIngestionConfig, EquityFetcher

# Custom configuration
config = DataIngestionConfig(
    cache_dir="/custom/path",
    default_ttl_seconds=7200,  # 2 hours
    rate_limit_per_second=1.5,
    max_retries=5,
    validate_data=True
)

# Use with fetcher
fetcher = EquityFetcher(config=config)
```

### Default Configuration Values

```python
cache_dir: ~/.quant_finance
default_ttl_seconds: 3600  # 1 hour
rate_limit_per_second: 2.0
rate_limit_burst: 10
max_retries: 3
validate_data: True
```

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

# Cached stock data fetcher
df = get_stock_data("AAPL", "2023-01-01", "2023-12-31")
st.dataframe(df)

# Cached options fetcher
calls, puts = get_options_chain("AAPL", "2024-01-19")
st.dataframe(calls)

# Display with error handling
df = display_fetch_status(
    get_stock_data,
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31"
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

# Complete stock data widget
df = create_stock_data_widget()
if df is not None:
    # Format and display metrics
    summary = format_market_data_summary(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("Latest Close", f"${summary['latest_close']:.2f}")
    col2.metric("Change", f"${summary['change']:.2f}", f"{summary['change_pct']:.2f}%")
    col3.metric("Period Return", f"{summary['period_return']:.2f}%")

    # Display chart
    st.line_chart(df['Close'])

# Options widget
result = create_options_widget()
if result:
    calls, puts = result
    st.subheader("Call Options")
    st.dataframe(calls)
```

## Error Handling

The package provides custom exceptions for different scenarios:

```python
from src.data_ingestion import (
    EquityFetcher,
    SymbolNotFoundError,
    ValidationError,
    RateLimitError,
    FetchError
)

fetcher = EquityFetcher()

try:
    df = fetcher.fetch_historical("INVALID_SYMBOL", "2023-01-01", "2023-12-31")
except SymbolNotFoundError as e:
    print(f"Symbol not found: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except FetchError as e:
    print(f"Failed to fetch data: {e}")
```

## Rate Limiting

Automatic rate limiting using token bucket algorithm:

```python
# Default: 2 requests/second with burst of 10
# Automatically throttles requests to respect API limits

fetcher = EquityFetcher()

# These calls will be automatically rate-limited
for symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]:
    df = fetcher.fetch_historical(symbol, "2023-01-01", "2023-12-31")
    print(f"Fetched {symbol}")
```

## Data Validation

Automatic data quality validation:

```python
# Equity data validation
# - Required columns exist (Open, High, Low, Close, Volume)
# - Prices are positive
# - High >= Low
# - No completely null rows

# Options data validation
# - Required columns exist (Strike, Last, Volume, OpenInterest)
# - Strikes are positive
# - Prices are non-negative

# Fixed income validation
# - Yields are non-negative
# - Yields are reasonable (< 100%)
```

## Advanced Usage

### Custom Retry Strategy

```python
from src.data_ingestion.utils.retry import ExponentialBackoffRetry

retry_strategy = ExponentialBackoffRetry(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0
)

# Use as decorator
@retry_strategy
def fetch_data():
    # Your fetch logic
    pass
```

### Cache Bypass

```python
# Bypass cache and force fresh fetch
df = fetcher.fetch_historical(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31",
    use_cache=False
)
```

### Cache Invalidation

```python
# Invalidate specific cache entry
fetcher.invalidate_cache(
    symbol="AAPL",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

## Package Structure

```
src/data_ingestion/
├── __init__.py                 # Package exports
├── config.py                   # Configuration management
├── exceptions.py               # Custom exceptions
├── base/
│   ├── fetcher.py             # Abstract base fetcher
│   └── cache.py               # Base cache interface
├── cache/
│   ├── duckdb_cache.py        # DuckDB caching
│   └── cache_manager.py       # Cache management
├── fetchers/
│   ├── equity.py              # Equity data fetcher
│   ├── options.py             # Options data fetcher
│   └── fixed_income.py        # Fixed income fetcher
├── utils/
│   ├── rate_limiter.py        # Rate limiting
│   ├── retry.py               # Retry logic
│   └── validators.py          # Data validation
└── streamlit_helpers.py       # Streamlit integration
```

## Performance Tips

1. **Use caching**: First call fetches from API, subsequent calls use cache
2. **Batch requests**: Use `fetch_multiple()` for multiple symbols
3. **Appropriate TTL**: Set longer TTL for historical data, shorter for recent data
4. **Cleanup regularly**: Run `manager.cleanup_expired_entries()` periodically
5. **Monitor cache size**: Check cache stats with `manager.get_cache_stats()`

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
from src.data_ingestion import DataIngestionConfig
config = DataIngestionConfig(rate_limit_per_second=1.0)
fetcher = EquityFetcher(config=config)
```

### Validation Errors

```python
# Allow partial data
from src.data_ingestion import DataIngestionConfig
config = DataIngestionConfig(allow_partial_data=True)
fetcher = EquityFetcher(config=config)
```

## License

MIT License - Part of the Quantitative Finance Project
