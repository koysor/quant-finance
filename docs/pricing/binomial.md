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

`binomial_price` keeps only the current step. `binomial_lattice` runs the same induction but returns every node: stock price, option value, whether an American option is exercised early there, and the replicating portfolio. `payoff` takes any function of \(S_T\), such as a digital or power payoff, in place of a vanilla call or put.

## Replication

Hold one option and short \(\Delta\) shares, \(\Pi = V - \Delta S\). The short position pays the dividends, so by the end of the step it owes \(e^{q\Delta t}\Delta\) shares. Choosing

\[
\Delta = e^{-q\Delta t}\,\frac{V^+ - V^-}{(u - d)S}
\]

makes \(\Pi\) worth the same after an up move (to \(V^+\)) and a down move (to \(V^-\)), so it is riskless. To avoid arbitrage it must then grow at the risk-free rate, \(\Pi e^{r\Delta t} = V^+ - e^{q\Delta t}\Delta uS\). With \(q = 0\) this is the textbook \(\Delta = (V^+ - V^-)/\big((u - d)S\big)\). Solving for \(V\) gives the backward induction formula above. The real-world probability of an up move, and the stock's drift \(\mu\), never appear: the price is the cost of replication. `BinomialLattice.delta` and `BinomialLattice.bond` hold \(\Delta\) and \(\Pi\) at each node. For an American option, \(\Pi\) is the cost of replicating the continuation value, which is less than the node's value where the holder exercises.

## Closed form

The number of up moves to expiry is \(\mathrm{Bin}(n, p)\) under the risk-neutral measure, so for a European option the induction collapses to one sum:

\[
V_0 = e^{-rT}\sum_{k=0}^{n}\binom{n}{k} p^k (1 - p)^{n-k}\,\text{Payoff}\big(S u^k d^{n-k}\big).
\]

`binomial_price_closed_form` evaluates it, and `terminal_distribution` returns the prices \(S u^k d^{n-k}\) and their probabilities. By the central limit theorem, \(\ln S_T\) on the tree tends to \(N\big(\ln S + (r - q - \tfrac{1}{2}\sigma^2)T,\ \sigma^2 T\big)\), the Black-Scholes distribution, which is why the price converges.

### Payoffs that jump at the strike

When \(K = S\) and \(n\) is even, the middle node at expiry is exactly \(S u^0 = K\): node prices are computed as \(S e^{k \ln u}\) for a net \(k\) up moves, so this node is not a rounding error above or below the strike. A payoff with a jump at \(K\), such as a digital, then needs a convention there. Paying 0 (or 1) biases the price by about half that node's probability, and since that probability shrinks only like \(1/\sqrt{n}\), so does the error. `digital_call_payoff` pays \(\tfrac{1}{2}\) on the strike, which removes most of the bias.

## Convergence

As \(n \to \infty\) the CRR price of a European option converges to the [Black-Scholes](black-scholes.md) price, with an error of order \(1/n\). At the money the error falls smoothly. Away from it the error is not monotone in \(n\): it depends on where the strike falls between the nodes at expiry, so it rises and falls as \(n\) changes while \(n \times \text{error}\) stays bounded. The test suite checks both. The Leisen-Reimer tree,[^lr] which places a node on the strike, converges smoothly at order \(1/n^2\).

## References

[^crr]: Cox, J. C., Ross, S. A. and Rubinstein, M. (1979). Option pricing: a simplified approach. *Journal of Financial Economics*, 7(3), 229–263.
[^lr]: Leisen, D. P. J. and Reimer, M. (1996). Binomial models for option valuation – examining and improving convergence. *Applied Mathematical Finance*, 3(4), 319–346.

## API

::: quant_finance.pricing.binomial
