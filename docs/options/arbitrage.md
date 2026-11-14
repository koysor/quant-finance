# Static arbitrage

`quant_finance.options.arbitrage` checks a strip of same-expiry option prices for static arbitrage: trades put on today and held to expiry that cost nothing or less and can never lose. The checks hold whatever the model.[^merton][^cm]

## Conditions

For European calls \(C(K)\) on one underlying with one expiry:

1. **Non-negative:** \(C(K) \ge 0\). An option is a right, not an obligation.
2. **Monotone:** \(C(K_1) \ge C(K_2)\) for \(K_1 < K_2\). The lower-strike call pays at least as much in every state.
3. **Bounded slope:** \(C(K_1) - C(K_2) \le K_2 - K_1\). The call spread pays at most \(K_2 - K_1\). The tight bound is \(e^{-rT}(K_2 - K_1)\), so the undiscounted bound used here flags only definite arbitrage, whatever the rate.
4. **Convex:** the slope between neighbouring strikes never falls:
   \[
   \frac{C(K_2) - C(K_1)}{K_2 - K_1} \le \frac{C(K_3) - C(K_2)}{K_3 - K_2}, \qquad K_1 < K_2 < K_3 .
   \]
   Otherwise a butterfly, which has a non-negative payoff, would cost less than nothing.

For puts, condition 2 reverses: puts get dearer as the strike rises. Conditions 1, 3 and 4 are unchanged.

## Why convexity matters

Differentiating the call price twice with respect to strike gives the risk-neutral density of \(S_T\):[^bl]

\[
\frac{\partial^2 C}{\partial K^2} = e^{-rT}\, f_{\mathbb{Q}}(K).
\]

A density cannot be negative, so convexity is the condition that the prices imply a valid distribution. It is the first thing to check before fitting a volatility surface.

## References

[^merton]: Merton, R. C. (1973). Theory of rational option pricing. *Bell Journal of Economics and Management Science*, 4(1), 141–183.
[^cm]: Carr, P. and Madan, D. B. (2005). A note on sufficient conditions for no arbitrage. *Finance Research Letters*, 2(3), 125–130.
[^bl]: Breeden, D. T. and Litzenberger, R. H. (1978). Prices of state-contingent claims implicit in option prices. *Journal of Business*, 51(4), 621–651.

## API

::: quant_finance.options.arbitrage
