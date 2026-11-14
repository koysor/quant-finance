# Binomial trees

`quant_finance.pricing.binomial` prices European and American options on a Cox-Ross-Rubinstein (CRR) tree.[^crr]

## Model

Split \([0, T]\) into \(n\) steps of length \(\Delta t = T/n\). At each step the stock moves up by a factor \(u\) or down by \(d\):

\[
u = e^{\sigma\sqrt{\Delta t}}, \qquad d = \frac{1}{u}, \qquad
p = \frac{e^{(r-q)\Delta t} - d}{u - d},
\]

where \(p\) is the risk-neutral probability of an up move. It is chosen so that the stock, with dividends reinvested, earns the risk-free rate in expectation. \(d = 1/u\) makes the tree recombine, so after \(j\) steps there are only \(j + 1\) nodes, \(S u^{j-i} d^{i}\) for \(i = 0, \dots, j\).

### No-arbitrage condition

\(p\) is a probability only when

\[
d < e^{(r-q)\Delta t} < u .
\]

Otherwise the stock beats the bank account in every state, or loses to it in every state, which is an arbitrage. With few steps, a high rate and low volatility this can fail. `crr_parameters` then raises and suggests more steps.

## Backward induction

At expiry each node is worth its payoff, \(\max(\phi(S_T - K), 0)\). Working back one step at a time, each node is worth the discounted risk-neutral expectation of its two successors:

\[
V_{j,i} = e^{-r\Delta t}\left(p\, V_{j+1,i} + (1-p)\, V_{j+1,i+1}\right).
\]

For an **American** option the holder can also exercise at any node, so its value is

\[
V_{j,i} = \max\!\left(e^{-r\Delta t}\left(p\, V_{j+1,i} + (1-p)\, V_{j+1,i+1}\right),\; \phi\,(S_{j,i} - K)\right).
\]

Without dividends, early exercise of an American call is never optimal, so its price equals the European price. American puts are worth more than European puts whenever \(r > 0\).

## Convergence

As \(n \to \infty\) the CRR price of a European option converges to the [Black-Scholes](black-scholes.md) price, with an error of order \(1/n\). At the money the error falls smoothly. Away from it the error is not monotone in \(n\): it depends on where the strike falls between the nodes at expiry, so it rises and falls as \(n\) changes while \(n \times \text{error}\) stays bounded. The test suite checks both. The Leisen-Reimer tree,[^lr] which places a node on the strike, converges smoothly at order \(1/n^2\).

## References

[^crr]: Cox, J. C., Ross, S. A. and Rubinstein, M. (1979). Option pricing: a simplified approach. *Journal of Financial Economics*, 7(3), 229–263.
[^lr]: Leisen, D. P. J. and Reimer, M. (1996). Binomial models for option valuation – examining and improving convergence. *Applied Mathematical Finance*, 3(4), 319–346.

## API

::: quant_finance.pricing.binomial
