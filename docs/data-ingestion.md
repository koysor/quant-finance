# Data ingestion

`quant_finance.data_ingestion` fetches market data with caching in DuckDB, rate limiting and retries with exponential backoff. Its usage guide is `src/quant_finance/data_ingestion/README.md`. This page is the API reference for the classes the package exports.

The Streamlit apps reach data through `quant_finance.data_ingestion.streamlit_helpers`, which wraps the fetchers in Streamlit's cache.

## Fetchers

::: quant_finance.data_ingestion.EquityFetcher

::: quant_finance.data_ingestion.OptionsFetcher

::: quant_finance.data_ingestion.FixedIncomeFetcher

## Cache

::: quant_finance.data_ingestion.DuckDBCache

::: quant_finance.data_ingestion.CacheManager

## Configuration

::: quant_finance.data_ingestion.DataIngestionConfig
