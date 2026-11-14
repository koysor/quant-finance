# Conventions

These hold across the library unless a function's docstring says otherwise.

## Units

| Quantity | Symbol | Unit |
|---|---|---|
| Time to expiry, horizon | \(T\), \(t\) | Years. \(T = 0.5\) is six months. |
| Interest rate | \(r\) | Continuously compounded, as a decimal: \(0.05\) is 5% a year. |
| Dividend yield | \(q\) | Continuously compounded, as a decimal. |
| Volatility | \(\sigma\) | Annualised, as a decimal: \(0.2\) is 20 vol points. |
| Treasury yields | | Percent, as FRED publishes them: \(4.25\) is 4.25%. |

A continuously compounded rate \(r\) discounts a cash flow \(X\) at time \(T\) to \(X e^{-rT}\). To convert from an annually compounded rate \(R\), use \(r = \ln(1 + R)\).

## Greeks

The Greeks are partial derivatives with respect to the raw inputs, so they are in the units of those inputs:

| Greek | Definition | To quote it the usual way |
|---|---|---|
| Delta | \(\partial V / \partial S\) | as is |
| Gamma | \(\partial^2 V / \partial S^2\) | as is |
| Vega | \(\partial V / \partial \sigma\) | divide by 100 for the change per vol point |
| Theta | \(\partial V / \partial t = -\partial V / \partial T\) | divide by 365 for the change per calendar day |
| Rho | \(\partial V / \partial r\) | divide by 100 for the change per percentage point |

## Arrays and broadcasting

Functions that take `ArrayLike` arguments broadcast them against each other with NumPy's rules, so a whole option chain, or a grid of spots and volatilities, prices in one call. A result from all-scalar inputs is a NumPy scalar.

## Edge cases

- A time to expiry of zero or below means the option has expired, and its value is the intrinsic value.
- With zero volatility the terminal price is known, so prices and Greeks are those of the discounted intrinsic value \(\max(S e^{-qT} - K e^{-rT}, 0)\) for a call.
- Inputs that make no sense, such as a negative strike or an unknown option type, raise `ValueError`.
- Solvers that are run over many inputs, such as `implied_volatility`, return NaN where there is no solution rather than raising, so one bad quote does not stop a whole chain.

## Randomness

Simulation functions take a `numpy.random.Generator` rather than seeding a global state. Pass `np.random.default_rng(seed)` for reproducible paths:

```python
import numpy as np
from quant_finance.stochastic.paths import gbm_paths

paths = gbm_paths(
    S0=100,
    mu=0.05,
    sigma=0.2,
    T=1,
    n_steps=252,
    n_paths=10_000,
    rng=np.random.default_rng(42),
)
```
