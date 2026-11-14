# Modern Portfolio Theory

`quant_finance.portfolio.mpt` computes the mean and variance of portfolio returns, and the frontier of portfolios made from two assets.[^markowitz]

## Mean and variance

For weights \(\mathbf{w}\) (summing to one), expected asset returns \(\boldsymbol{\mu}\) and covariance matrix \(\Sigma\):

\[
\mu_p = \mathbf{w}^\top \boldsymbol{\mu}, \qquad \sigma_p^2 = \mathbf{w}^\top \Sigma\, \mathbf{w}.
\]

The covariance matrix can be built from volatilities \(\sigma_i\) and correlations \(\rho_{ij}\) as \(\Sigma_{ij} = \rho_{ij}\sigma_i\sigma_j\), or \(\Sigma = D R D\) with \(D = \operatorname{diag}(\sigma)\).

## Two assets

With weight \(w\) in asset 1 and \(1 - w\) in asset 2:

\[
\sigma_p^2 = w^2\sigma_1^2 + (1-w)^2\sigma_2^2 + 2w(1-w)\rho\,\sigma_1\sigma_2 .
\]

Setting the derivative with respect to \(w\) to zero gives the minimum-variance weight

\[
w^* = \frac{\sigma_2^2 - \rho\,\sigma_1\sigma_2}{\sigma_1^2 + \sigma_2^2 - 2\rho\,\sigma_1\sigma_2}.
\]

`two_asset_min_variance_weight` clips \(w^*\) to \([0, 1]\), so it gives the minimum-variance portfolio without short selling.

Diversification is the gap between \(\sigma_p\) and the weighted average \(w\sigma_1 + (1-w)\sigma_2\). The gap is zero when \(\rho = 1\) and widest when \(\rho = -1\). At \(\rho = -1\), \(w = \sigma_2 / (\sigma_1 + \sigma_2)\) gives a riskless portfolio.

## Assumptions

Investors care only about the mean and variance of returns over one period. That is justified if returns are normal or utility is quadratic. The inputs \(\boldsymbol{\mu}\) and \(\Sigma\) are taken as known, but in practice they are estimated, and optimised weights are very sensitive to errors in \(\boldsymbol{\mu}\).[^michaud]

## References

[^markowitz]: Markowitz, H. (1952). Portfolio selection. *Journal of Finance*, 7(1), 77–91.
[^michaud]: Michaud, R. O. (1989). The Markowitz optimization enigma: is 'optimized' optimal? *Financial Analysts Journal*, 45(1), 31–42.

## API

::: quant_finance.portfolio.mpt
