# Stochastic processes

`quant_finance.stochastic.paths` simulates sample paths of three processes. Every function returns an array of shape `(n_paths, n_steps + 1)`, one row per path, with the starting value in column 0. Every function takes a `numpy.random.Generator`, so results are reproducible (see [Conventions](../conventions.md#randomness)).

## Wiener process

A standard Wiener process (Brownian motion) \(W_t\) has:

- \(W_0 = 0\);
- independent increments: \(W_{t} - W_{s}\) is independent of the path up to \(s\);
- normal increments: \(W_{t} - W_{s} \sim N(0,\, t - s)\);
- continuous paths.

`wiener_paths` draws independent \(N(0, \Delta t)\) increments and adds them up, which samples \(W\) exactly at the grid points. It follows that \(\mathbb{E}[W_t] = 0\) and \(\operatorname{Var}(W_t) = t\).

## Geometric Brownian motion

The stock price model behind [Black-Scholes](../pricing/black-scholes.md) is

\[
dS_t = \mu S_t\, dt + \sigma S_t\, dW_t .
\]

By Itô's lemma, \(d \ln S_t = (\mu - \tfrac{1}{2}\sigma^2)\, dt + \sigma\, dW_t\), so

\[
S_t = S_0 \exp\!\left( \left(\mu - \tfrac{1}{2}\sigma^2\right) t + \sigma W_t \right).
\]

`gbm_paths` steps this exact solution:

\[
S_{t + \Delta t} = S_t \exp\!\left( \left(\mu - \tfrac{1}{2}\sigma^2\right) \Delta t + \sigma \sqrt{\Delta t}\, Z \right), \qquad Z \sim N(0, 1).
\]

Unlike an Euler step, \(S_{t+\Delta t} = S_t(1 + \mu \Delta t + \sigma\sqrt{\Delta t}\, Z)\), this has no discretisation error and never goes negative, whatever \(\Delta t\). Its moments are

\[
\mathbb{E}[S_t] = S_0 e^{\mu t}, \qquad
\operatorname{Var}(S_t) = S_0^2 e^{2\mu t}\left(e^{\sigma^2 t} - 1\right).
\]

The \(-\tfrac{1}{2}\sigma^2\) term is the Itô correction. Without it the mean would be \(S_0 e^{(\mu + \sigma^2/2)t}\). The median of \(S_t\) is \(S_0 e^{(\mu - \sigma^2/2)t}\), below the mean, because the lognormal distribution is skewed to the right.

To simulate under the risk-neutral measure, set \(\mu = r - q\).

## Random walk

`random_walk_paths` moves \(+1\) with probability \(p\) and \(-1\) with probability \(1 - p\) at each step, so

\[
\mathbb{E}[X_n] = X_0 + n(2p - 1), \qquad \operatorname{Var}(X_n) = 4 n p (1 - p).
\]

It is a martingale when \(p = \tfrac{1}{2}\), a sub-martingale when \(p > \tfrac{1}{2}\) and a super-martingale when \(p < \tfrac{1}{2}\). Scaled by \(\sqrt{\Delta t}\) with \(p = \tfrac{1}{2}\), it converges to a Wiener process as \(\Delta t \to 0\) (Donsker's theorem).

## Monte Carlo error

An average over \(M\) independent paths has a standard error of \(s / \sqrt{M}\), where \(s\) is the sample standard deviation. Halving the error takes four times as many paths. Variance reduction, such as antithetic variates or control variates, is the way to do better than that.[^glasserman]

## References

[^glasserman]: Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering*. Springer, chapters 3 and 4.

Shreve, S. E. (2004). *Stochastic Calculus for Finance II: Continuous-Time Models*. Springer, chapters 3 and 4, covers Brownian motion and Itô's lemma.

## API

::: quant_finance.stochastic.paths
