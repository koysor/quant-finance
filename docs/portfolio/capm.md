# CAPM

`quant_finance.portfolio.capm` gives expected returns under the Capital Asset Pricing Model, and Jensen's alpha against them.[^sharpe][^lintner]

## The model

\[
\mathbb{E}[R_i] = R_f + \beta_i\left(\mathbb{E}[R_m] - R_f\right),
\qquad
\beta_i = \frac{\operatorname{Cov}(R_i, R_m)}{\operatorname{Var}(R_m)} .
\]

Only systematic risk, measured by \(\beta_i\), earns a premium. Idiosyncratic risk can be diversified away, so the market does not pay for it. Plotting \(\mathbb{E}[R_i]\) against \(\beta_i\) gives the security market line, which passes through \((0, R_f)\) and \((1, \mathbb{E}[R_m])\).

## Assumptions

- Investors choose portfolios by mean and variance over one period (see [Modern Portfolio Theory](mpt.md)), and agree on the expected returns and covariances.
- Everyone can borrow and lend without limit at the risk-free rate \(R_f\).
- There are no taxes or transaction costs, and assets are infinitely divisible.

Under these assumptions every investor holds the market portfolio combined with the risk-free asset.

## Jensen's alpha

\[
\alpha_i = R_i - \left(R_f + \beta_i (R_m - R_f)\right)
\]

is the return in excess of what CAPM predicts for the asset's beta.[^jensen] A positive alpha suggests outperformance, but only if CAPM is the right benchmark. Multi-factor models, such as Fama-French, often explain apparent alpha.

Keep the units consistent: `risk_free_rate`, `market_return` and `actual_return` must all be over the same period, either all annual or all monthly.

## References

[^sharpe]: Sharpe, W. F. (1964). Capital asset prices: a theory of market equilibrium under conditions of risk. *Journal of Finance*, 19(3), 425–442.
[^lintner]: Lintner, J. (1965). The valuation of risk assets and the selection of risky investments in stock portfolios and capital budgets. *Review of Economics and Statistics*, 47(1), 13–37.
[^jensen]: Jensen, M. C. (1968). The performance of mutual funds in the period 1945–1964. *Journal of Finance*, 23(2), 389–416.

## API

::: quant_finance.portfolio.capm
