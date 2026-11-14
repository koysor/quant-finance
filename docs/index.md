# quant_finance

`quant_finance` is the library behind the Streamlit apps in this repository. Each page of these docs covers one module: first the model, its assumptions and its formulas, then the API reference generated from the code's docstrings.

| Area | Module | What it covers |
|---|---|---|
| [Black-Scholes-Merton](pricing/black-scholes.md) | `quant_finance.pricing.black_scholes` | European prices, Greeks and implied volatility |
| [Binomial trees](pricing/binomial.md) | `quant_finance.pricing.binomial` | Cox-Ross-Rubinstein trees for European and American options |
| [Put-call parity](pricing/parity.md) | `quant_finance.pricing.parity` | The model-free link between European calls and puts |
| [Payoffs](options/payoffs.md) | `quant_finance.options.payoffs` | Single options and multi-leg strategies at expiry |
| [Static arbitrage](options/arbitrage.md) | `quant_finance.options.arbitrage` | Model-free checks on a strip of option prices |
| [Stochastic processes](stochastic/paths.md) | `quant_finance.stochastic.paths` | Simulated GBM, Wiener and random-walk paths |
| [Modern Portfolio Theory](portfolio/mpt.md) | `quant_finance.portfolio.mpt` | Portfolio mean and variance, the two-asset frontier |
| [CAPM](portfolio/capm.md) | `quant_finance.portfolio.capm` | Expected returns and Jensen's alpha |
| [Treasury yield curve](rates/treasury.md) | `quant_finance.rates.treasury` | Constant-maturity par yields from FRED |
| [Data ingestion](data-ingestion.md) | `quant_finance.data_ingestion` | Cached, rate-limited market data fetchers |

Read [Conventions](conventions.md) first: it sets out the units and the edge-case behaviour that every module shares.

## Building these docs

The site is built with [Zensical](https://zensical.org) and published at <https://koysor.github.io/quant-finance/docs/>, next to the marimo notebooks, whenever `main` changes.

```bash
uv run --group docs zensical serve   # live preview at http://localhost:8000
scripts/build_docs.sh                # what CI runs; any warning fails the build
```
