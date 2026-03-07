# Data Ingestion API Reference

Key fetchers available in `src.data_ingestion`.

## EquityFetcher
```python
from src.data_ingestion import EquityFetcher
fetcher = EquityFetcher()

# Historical OHLCV
df = fetcher.fetch_historical(symbol="AAPL", start_date="2024-01-01")

# Multiple symbols
data = fetcher.fetch_multiple(symbols=["AAPL", "MSFT"]) # returns {symbol: df}

# Real-time quote
quote = fetcher.fetch_realtime_quote("AAPL") # returns dict

# Info/Fundamentals
info = fetcher.get_info("AAPL") # returns dict
```

## OptionsFetcher
```python
from src.data_ingestion import OptionsFetcher
fetcher = OptionsFetcher()

# Expirations
expirations = fetcher.get_available_expirations("AAPL")

# Option chain
calls, puts = fetcher.fetch_option_chain("AAPL", expiration="2025-01-17")

# Greeks (with BSM)
calls_with_greeks = fetcher.fetch_greeks("AAPL", expiration="2025-01-17", option_type="call")
```

## FixedIncomeFetcher
```python
from src.data_ingestion import FixedIncomeFetcher
fetcher = FixedIncomeFetcher()

# Treasury yields (time series)
yields_df = fetcher.fetch_treasury_yields(maturities=["2Y", "10Y"])

# Yield curve (snapshot)
curve = fetcher.fetch_yield_curve(date="2024-12-20")
```
