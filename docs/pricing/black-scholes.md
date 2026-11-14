# Black-Scholes-Merton

`quant_finance.pricing.black_scholes` prices European calls and puts on a stock that pays a continuous dividend yield, together with their Greeks and implied volatility. With \(q = 0\) these are the original Black-Scholes formulas.[^bs][^merton]

## Model

Under the risk-neutral measure \(\mathbb{Q}\), the stock follows geometric Brownian motion

\[
dS_t = (r - q)\, S_t\, dt + \sigma\, S_t\, dW_t^{\mathbb{Q}},
\]

so \(\ln S_T\) is normal and the price of a claim paying \(V(S_T)\) at \(T\) is \(e^{-rT}\,\mathbb{E}^{\mathbb{Q}}[V(S_T)]\).

### Assumptions

- The volatility \(\sigma\), the rate \(r\) and the dividend yield \(q\) are constant over the life of the option.
- Trading is continuous, with no transaction costs, taxes or short-selling limits, and the asset is infinitely divisible.
- Borrowing and lending are at the same rate \(r\).
- There is no arbitrage.
- The option is European: it can be exercised only at expiry. For early exercise, use a [binomial tree](binomial.md).

Markets break most of these. The clearest symptom is the volatility smile: the \(\sigma\) that matches market prices changes with strike and expiry, where the model says it should be one number.

## Prices

With

\[
d_1 = \frac{\ln(S/K) + (r - q + \tfrac{1}{2}\sigma^2)\,T}{\sigma\sqrt{T}},
\qquad
d_2 = d_1 - \sigma\sqrt{T},
\]

the call and put prices are

\[
C = S e^{-qT} N(d_1) - K e^{-rT} N(d_2),
\qquad
P = K e^{-rT} N(-d_2) - S e^{-qT} N(-d_1),
\]

where \(N\) is the standard normal distribution function and \(n\) its density. \(N(d_2)\) is the risk-neutral probability that a call finishes in the money; \(e^{-qT}N(d_1)\) is its delta.

## Greeks

With \(\phi = 1\) for a call and \(\phi = -1\) for a put:

| Greek | Formula |
|---|---|
| Delta \(\Delta\) | \(\phi\, e^{-qT} N(\phi d_1)\) |
| Gamma \(\Gamma\) | \(\dfrac{e^{-qT}\, n(d_1)}{S \sigma \sqrt{T}}\), the same for calls and puts |
| Vega \(\mathcal{V}\) | \(S e^{-qT}\, n(d_1) \sqrt{T}\), the same for calls and puts |
| Theta \(\Theta\) | \(-\dfrac{S e^{-qT}\, n(d_1)\, \sigma}{2\sqrt{T}} + \phi\left(q S e^{-qT} N(\phi d_1) - r K e^{-rT} N(\phi d_2)\right)\) |
| Rho \(\rho\) | \(\phi\, K T e^{-rT} N(\phi d_2)\) |

See [Conventions](../conventions.md#greeks) for the units. The Greeks satisfy the Black-Scholes PDE,

\[
\Theta + (r - q) S \Delta + \tfrac{1}{2}\sigma^2 S^2 \Gamma = r V,
\]

which the test suite checks.

## Limits

When \(\sigma\sqrt{T} = 0\), because the option has expired or there is no volatility, \(S_T\) is known and \(d_1, d_2 \to \pm\infty\). The library then returns the discounted intrinsic value, \(\max\!\left(\phi(S e^{-qT} - K e^{-rT}), 0\right)\), instead of dividing by zero.

## Implied volatility

The implied volatility is the \(\sigma\) at which the model price equals a market price. Because vega is positive, the price rises strictly with \(\sigma\), so there is at most one solution. It exists only inside the no-arbitrage bounds

\[
\max(S e^{-qT} - K e^{-rT}, 0) < C < S e^{-qT},
\qquad
\max(K e^{-rT} - S e^{-qT}, 0) < P < K e^{-rT}.
\]

`implied_volatility` finds the root with Brent's method[^brent] on a bracket, \([10^{-6}, 5]\) by default, and returns NaN for prices outside it. Deep in the money, vega is so small that prices at low volatilities equal the intrinsic value to machine precision. No volatility can be recovered there either, and the function returns NaN rather than an arbitrary number.

## References

[^bs]: Black, F. and Scholes, M. (1973). The pricing of options and corporate liabilities. *Journal of Political Economy*, 81(3), 637–654.
[^merton]: Merton, R. C. (1973). Theory of rational option pricing. *Bell Journal of Economics and Management Science*, 4(1), 141–183.
[^brent]: Brent, R. P. (1973). *Algorithms for Minimization without Derivatives*. Prentice-Hall, chapter 4.

Hull, J. C. (2022). *Options, Futures, and Other Derivatives*, 11th ed., chapters 15 and 19, covers the same ground with worked examples. Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas*, 2nd ed., gives reference values that the tests use.

## API

::: quant_finance.pricing.black_scholes
